from pprint import pprint
from typing import Optional

import py

from _pytest._code.code import ExceptionInfo
from _pytest._code.code import ReprEntry
from _pytest._code.code import ReprEntryNative
from _pytest._code.code import ReprExceptionInfo
from _pytest._code.code import ExceptionChainRepr
from _pytest._code.code import ReprFileLocation
from _pytest._code.code import ReprFuncArgs
from _pytest._code.code import ReprLocals
from _pytest._code.code import ReprTraceback
from _pytest._code.code import TerminalRepr
from _pytest.outcomes import skip
from _pytest.pathlib import Path


def getslaveinfoline(node):
    try:
        return node._slaveinfocache
    except AttributeError:
        d = node.slaveinfo
        ver = "%s.%s.%s" % d["version_info"][:3]
        node._slaveinfocache = s = "[{}] {} -- Python {} {}".format(
            d["id"], d["sysplatform"], ver, d["executable"]
        )
        return s


class BaseReport:
    when = None  # type: Optional[str]
    location = None

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def toterminal(self, out):
        if hasattr(self, "node"):
            out.line(getslaveinfoline(self.node))

        longrepr = self.longrepr
        if longrepr is None:
            return

        if hasattr(longrepr, "toterminal"):
            longrepr.toterminal(out)
        else:
            try:
                out.line(longrepr)
            except UnicodeEncodeError:
                out.line("<unprintable longrepr>")

    def get_sections(self, prefix):
        for name, content in self.sections:
            if name.startswith(prefix):
                yield prefix, content

    @property
    def longreprtext(self):
        """
        Read-only property that returns the full string representation
        of ``longrepr``.

        .. versionadded:: 3.0
        """
        tw = py.io.TerminalWriter(stringio=True)
        tw.hasmarkup = False
        self.toterminal(tw)
        exc = tw.stringio.getvalue()
        return exc.strip()

    @property
    def caplog(self):
        """Return captured log lines, if log capturing is enabled

        .. versionadded:: 3.5
        """
        return "\n".join(
            content for (prefix, content) in self.get_sections("Captured log")
        )

    @property
    def capstdout(self):
        """Return captured text from stdout, if capturing is enabled

        .. versionadded:: 3.0
        """
        return "".join(
            content for (prefix, content) in self.get_sections("Captured stdout")
        )

    @property
    def capstderr(self):
        """Return captured text from stderr, if capturing is enabled

        .. versionadded:: 3.0
        """
        return "".join(
            content for (prefix, content) in self.get_sections("Captured stderr")
        )

    passed = property(lambda x: x.outcome == "passed")
    failed = property(lambda x: x.outcome == "failed")
    skipped = property(lambda x: x.outcome == "skipped")

    @property
    def fspath(self):
        return self.nodeid.split("::")[0]

    @property
    def count_towards_summary(self):
        """
        **Experimental**

        Returns True if this report should be counted towards the totals shown at the end of the
        test session: "1 passed, 1 failure, etc".

        .. note::

            This function is considered **experimental**, so beware that it is subject to changes
            even in patch releases.
        """
        return True

    @property
    def head_line(self):
        """
        **Experimental**

        Returns the head line shown with longrepr output for this report, more commonly during
        traceback representation during failures::

            ________ Test.foo ________


        In the example above, the head_line is "Test.foo".

        .. note::

            This function is considered **experimental**, so beware that it is subject to changes
            even in patch releases.
        """
        if self.location is not None:
            fspath, lineno, domain = self.location
            return domain

    def _get_verbose_word(self, config):
        _category, _short, verbose = config.hook.pytest_report_teststatus(
            report=self, config=config
        )
        return verbose

    def _to_json(self):
        """
        This was originally the serialize_report() function from xdist (ca03269).

        Returns the contents of this report as a dict of builtin entries, suitable for
        serialization.

        Experimental method.
        """

        def _serialize_reprtraceback(reprtraceback):
            data = reprtraceback.__dict__.copy()
            new_entries = []
            for entry in data["reprentries"]:
                entry_data = {
                    "type": type(entry).__name__,
                    "data": entry.__dict__.copy(),
                }
                # nested repr components (ReprFuncArgs, ReprLocals, ReprFileLocation)
                for key, value in entry_data["data"].items():
                    if hasattr(value, "__dict__"):
                        entry_data["data"][key] = value.__dict__.copy()
                new_entries.append(entry_data)
            data["reprentries"] = new_entries
            return data

        def disassembled_report(rep):
            # Always include outermost exception for backwards compatibility
            reprtraceback = _serialize_reprtraceback(rep.longrepr.reprtraceback)
            reprcrash = rep.longrepr.reprcrash.__dict__.copy()

            assembled = {
                "reprcrash": reprcrash,
                "reprtraceback": reprtraceback,
                "sections": rep.longrepr.sections,
            }

            # Optional: include full exception chain if available
            chain = getattr(rep.longrepr, "chain", None)
            if chain:
                serialized_chain = []
                for repr_tb, repr_crash, descr in chain:
                    serialized_chain.append(
                        {
                            "reprtraceback": _serialize_reprtraceback(repr_tb),
                            "reprcrash": (
                                repr_crash.__dict__.copy() if repr_crash else None
                            ),
                            "descr": descr,
                        }
                    )
                assembled["chain"] = serialized_chain

            return assembled

        d = self.__dict__.copy()
        if hasattr(self.longrepr, "toterminal"):
            if hasattr(self.longrepr, "reprtraceback") and hasattr(
                self.longrepr, "reprcrash"
            ):
                d["longrepr"] = disassembled_report(self)
            else:
                d["longrepr"] = str(self.longrepr)
        else:
            d["longrepr"] = self.longrepr
        for name in d:
            if isinstance(d[name], (py.path.local, Path)):
                d[name] = str(d[name])
            elif name == "result":
                d[name] = None  # for now
        return d

    @classmethod
    def _from_json(cls, reportdict):
        """
        This was originally the serialize_report() function from xdist (ca03269).

        Factory method that returns either a TestReport or CollectReport, depending on the calling
        class. It's the callers responsibility to know which class to pass here.

        Experimental method.
        """
        if reportdict["longrepr"]:
            if (
                "reprcrash" in reportdict["longrepr"]
                and "reprtraceback" in reportdict["longrepr"]
            ):

                def _deserialize_reprtraceback(data):
                    unserialized_entries = []
                    reprentry = None
                    for entry_data in data["reprentries"]:
                        entry = entry_data["data"]
                        entry_type = entry_data["type"]
                        if entry_type == "ReprEntry":
                            reprfuncargs = None
                            reprfileloc = None
                            reprlocals = None
                            if entry["reprfuncargs"]:
                                reprfuncargs = ReprFuncArgs(**entry["reprfuncargs"])
                            if entry["reprfileloc"]:
                                reprfileloc = ReprFileLocation(**entry["reprfileloc"])
                            if entry["reprlocals"]:
                                reprlocals = ReprLocals(entry["reprlocals"]["lines"])

                            reprentry = ReprEntry(
                                lines=entry["lines"],
                                reprfuncargs=reprfuncargs,
                                reprlocals=reprlocals,
                                filelocrepr=reprfileloc,
                                style=entry["style"],
                            )
                        elif entry_type == "ReprEntryNative":
                            reprentry = ReprEntryNative(entry["lines"])
                        else:
                            _report_unserialization_failure(entry_type, cls, reportdict)
                        unserialized_entries.append(reprentry)
                    data["reprentries"] = unserialized_entries
                    return ReprTraceback(**data)

                reprtraceback_data = reportdict["longrepr"]["reprtraceback"]
                reprcrash_data = reportdict["longrepr"]["reprcrash"]

                # By default, construct a single exception representation
                reprtraceback_obj = _deserialize_reprtraceback(reprtraceback_data)
                reprcrash_obj = ReprFileLocation(**reprcrash_data)

                longrepr_dict = reportdict["longrepr"]
                if "chain" in longrepr_dict and longrepr_dict["chain"]:
                    # Full chained exception representation
                    chain_list = []
                    for element in longrepr_dict["chain"]:
                        rt_obj = _deserialize_reprtraceback(element["reprtraceback"])
                        rc_obj = (
                            ReprFileLocation(**element["reprcrash"]) if element["reprcrash"] else None
                        )
                        descr = element.get("descr")
                        chain_list.append((rt_obj, rc_obj, descr))
                    exception_info = ExceptionChainRepr(chain_list)
                else:
                    exception_info = ReprExceptionInfo(
                        reprtraceback=reprtraceback_obj,
                        reprcrash=reprcrash_obj,
                    )

                for section in longrepr_dict["sections"]:
                    exception_info.addsection(*section)
                reportdict["longrepr"] = exception_info

        return cls(**reportdict)


def _report_unserialization_failure(type_name, report_class, reportdict):
    url = "https://github.com/pytest-dev/pytest/issues"
    stream = py.io.TextIO()
    pprint("-" * 100, stream=stream)
    pprint("INTERNALERROR: Unknown entry type returned: %s" % type_name, stream=stream)
    pprint("report_name: %s" % report_class, stream=stream)
    pprint(reportdict, stream=stream)
    pprint("Please report this bug at %s" % url, stream=stream)
    pprint("-" * 100, stream=stream)
    raise RuntimeError(stream.getvalue())


class TestReport(BaseReport):
    """ Basic test report object (also used for setup and teardown calls if
    they fail).
    """

    __test__ = False

    def __init__(
        self,
        nodeid,
        location,
        keywords,
        outcome,
        longrepr,
        when,
        sections=(),
        duration=0,
        user_properties=None,
        **extra
    ):
        #: normalized collection node id
        self.nodeid = nodeid

        #: a (filesystempath, lineno, domaininfo) tuple indicating the
        #: actual location of a test item - it might be different from the
        #: collected one e.g. if a method is inherited from a different module.
        self.location = location

        #: a name -> value dictionary containing all keywords and
        #: markers associated with a test invocation.
        self.keywords = keywords

        #: test outcome, always one of "passed", "failed", "skipped".
        self.outcome = outcome

        #: None or a failure representation.
        self.longrepr = longrepr

        #: one of 'setup', 'call', 'teardown' to indicate runtest phase.
        self.when = when

        #: user properties is a list of tuples (name, value) that holds user
        #: defined properties of the test
        self.user_properties = list(user_properties or [])

        #: list of pairs ``(str, str)`` of extra information which needs to
        #: marshallable. Used by pytest to add captured text
        #: from ``stdout`` and ``stderr``, but may be used by other plugins
        #: to add arbitrary information to reports.
        self.sections = list(sections)

        #: time it took to run just the test
        self.duration = duration

        self.__dict__.update(extra)

    def __repr__(self):
        return "<{} {!r} when={!r} outcome={!r}>".format(
            self.__class__.__name__, self.nodeid, self.when, self.outcome
        )

    @classmethod
    def from_item_and_call(cls, item, call):
        """
        Factory method to create and fill a TestReport with standard item and call info.
        """
        when = call.when
        duration = call.stop - call.start
        keywords = {x: 1 for x in item.keywords}
        excinfo = call.excinfo
        sections = []
        if not call.excinfo:
            outcome = "passed"
            longrepr = None
        else:
            if not isinstance(excinfo, ExceptionInfo):
                outcome = "failed"
                longrepr = excinfo
            elif excinfo.errisinstance(skip.Exception):
                outcome = "skipped"
                r = excinfo._getreprcrash()
                longrepr = (str(r.path), r.lineno, r.message)
            else:
                outcome = "failed"
                if call.when == "call":
                    longrepr = item.repr_failure(excinfo)
                else:  # exception in setup or teardown
                    longrepr = item._repr_failure_py(
                        excinfo, style=item.config.getoption("tbstyle", "auto")
                    )
        for rwhen, key, content in item._report_sections:
            sections.append(("Captured {} {}".format(key, rwhen), content))
        return cls(
            item.nodeid,
            item.location,
            keywords,
            outcome,
            longrepr,
            when,
            sections,
            duration,
            user_properties=item.user_properties,
        )


class CollectReport(BaseReport):
    when = "collect"

    def __init__(self, nodeid, outcome, longrepr, result, sections=(), **extra):
        self.nodeid = nodeid
        self.outcome = outcome
        self.longrepr = longrepr
        self.result = result or []
        self.sections = list(sections)
        self.__dict__.update(extra)

    @property
    def location(self):
        return (self.fspath, None, self.fspath)

    def __repr__(self):
        return "<CollectReport {!r} lenresult={} outcome={!r}>".format(
            self.nodeid, len(self.result), self.outcome
        )


class CollectErrorRepr(TerminalRepr):
    def __init__(self, msg):
        self.longrepr = msg

    def toterminal(self, out):
        out.line(self.longrepr, red=True)


def pytest_report_to_serializable(report):
    if isinstance(report, (TestReport, CollectReport)):
        data = report._to_json()
        data["_report_type"] = report.__class__.__name__
        return data


def pytest_report_from_serializable(data):
    if "_report_type" in data:
        if data["_report_type"] == "TestReport":
            return TestReport._from_json(data)
        elif data["_report_type"] == "CollectReport":
            return CollectReport._from_json(data)
        assert False, "Unknown report_type unserialize data: {}".format(
            data["_report_type"]
        )
