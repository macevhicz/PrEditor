#!/usr/bin/env python

# standard library imports
from collections import OrderedDict
from datetime import datetime
import os
import traceback
import sys
import platform
import socket
import string

# blur imports
import blurdev
from blurdev.contexts import ErrorReport

_host_information = None
_user_information = None
_environment_information = None


def get_host_information(refresh=False):
    """
    Aggreates several sources of host metadata, constructing an informative
    dictionary. Example information: hostname, operating system, ip address,
    host type (i.e. farm server vs. workstation).

    Information is gathered only once per runtime and stored globally. One may
    force a refresh by setting the `refresh` argument to True.

    Args:
        refresh (bool, optional): force refresh of all host information

    Returns:
        OrderedDict: various data regarding current host
    """

    global _host_information

    if _host_information is None or refresh:

        hostname = socket.gethostname()
        _host_information = OrderedDict(
            [
                ("hostname", hostname),
                ("ip_address", socket.gethostbyname(hostname)),
                ("host_type", platform.node().strip(string.digits)),
                ("os", platform.system()),
                ("os.release", platform.release()),
                ("os.version", platform.version()),
            ]
        )

    return _host_information


def get_user_information(refresh=False):
    """
    Gathers information about the current user. Will attempt to query data
    from Trax otherwise falling back to the current user logged onto host.

    Information is gathered only once per runtime and stored globally. One may
    force a refresh by setting the `refresh` argument to True.

    Args:
        refresh (bool, optional): force refresh of all user information

    Returns:
        OrderedDict: various data regarding current user
    """
    global _user_information

    if _user_information is None or refresh:

        try:
            from trax.api.data import User, Employee

        # trax not importable
        except ImportError:
            import getpass

            _user_information = OrderedDict([("username", getpass.getuser())])

        # successful import
        else:
            _user_information = OrderedDict()
            user = User.currentUser()
            if user.isRecord() and isinstance(user, Employee):
                _user_information["name"] = user.fullName()
                _user_information["username"] = user.username()
                _user_information["email"] = user.email()

            # non-employee users lack name and email fields
            else:
                _user_information["username"] = user.username()

    return _user_information


def get_environment_information(refresh=False):
    """
    Supplies a dictionary of runtime environment information, such as:
    core application, active environment, executable, and python version.
    Conditionally, additional information regarding core-specific messages,
    burner jobs, and/or Qt, may be supplied.

    Information is gathered only once per runtime and stored globally. One may
    force a refresh by setting the `refresh` argument to True.

    Args:
        refresh (bool, optional): force refresh of all environment information

    Returns:
        OrderedDict: various data regarding environment
    """
    global _environment_information

    if _environment_information is None or refresh:

        active_environment = blurdev.activeEnvironment()
        _environment_information = OrderedDict(
            [
                ("core", blurdev.core.objectName()),
                ("environment", active_environment.objectName()),
                ("environment.path", active_environment.path()),
                ("exe", sys.executable),
                ("python", "{}.{}.{}".format(*sys.version_info[:3])),
            ]
        )

        # burner job info
        burner_information = OrderedDict(
            [
                ("burn.jobid", os.environ.get("AB_JOBID", None)),
                ("burn.dir", os.environ.get("AB_BURNDIR", None)),
                ("burn.file", os.environ.get("AB_BURNFILE", None)),
            ]
        )
        for key, value in burner_information.items():
            if value:
                _environment_information[key] = value

        # miscellaneous email info
        prefix = "BDEV_EMAILINFO_"
        for key, value in os.environ.items():
            if key.startswith(prefix) and value:
                trimmed_key = key.replace(prefix, "").lower()
                _environment_information[trimmed_key] = value

        # core-specific message
        core_message = blurdev.core.errorCoreText()
        if core_message:
            _environment_information["core.message"] = core_message

        # root application window
        if not blurdev.core.headless:
            from Qt.QtWidgets import QApplication

            window = QApplication.activeWindow()

            if window is not None:
                window_class = window.__class__.__name__

                if window_class in ("LoggerWindow", "ErrorDialog"):
                    window = window.parent()
                    window_class = window.__class__.__name__

                if hasattr(window, "objectName"):
                    _environment_information["window"] = window.objectName()
                    _environment_information["window.class"] = window_class

    return _environment_information


def get_error_reports():
    """
    Supplies a list of any reports generated by the `ErrorReport` decorator.

    Returns:
        list/None: list of tuples with the the error report title and report
            contents as members
    """
    reports = ErrorReport.generateReport()
    if reports:
        return reports
    return None


def all_information_by_section(refresh=False):
    """
    Convenience function to return a dictionary of each section's dictionary of
    relevant debug information.

    Note: Information is gathered only once per runtime and stored globally.
          One may force a refresh by setting the `refresh` argument to True.

    Args:
        refresh (bool, optional): force refresh of all environment information

    Returns:
        OrderedDict: section names as keys, section information dictionaries as values
    """
    info_functions = (
        ("user", get_user_information),
        ("host", get_host_information),
        ("environment", get_environment_information),
    )

    information_dictionary = OrderedDict()
    for label, func in info_functions:
        results = func(refresh)
        if results:
            information_dictionary[label] = results

    return information_dictionary


def all_information(refresh=False):
    """
    Convenience function to return a flattened version of all sessions'
    relevate debug information dictionaries.

    Note: Information is gathered only once per runtime and stored globally.
          One may force a refresh by setting the `refresh` argument to True.

    Args:
        refresh (bool, optional): force refresh of all environment information

    Returns:
        OrderedDict: debug information
    """
    information_dictionary = OrderedDict()
    for section_dictionary in all_information_by_section(refresh).values():
        information_dictionary.update(section_dictionary)
    return information_dictionary


def highlight_code(code, linenos=False):
    """
    Given a formatted traceback, return syntax-highlighted HTML codeblock with
    inline CSS styles.

    Args:
        code (list): pre-formatted stack trace with exception information;
            created via `traceback.format_exception`
        linenos (str/bool): manor in which line numbers will be presented;
            options: `inline` (default), `table`, or False

    Returns:
        str: valid HTML of syntax-highlighted exception with inline styles
    """
    import pygments
    from pygments.lexers.python import PythonTracebackLexer
    from pygments.formatters import HtmlFormatter

    formatted_code = pygments.highlight(
        "".join(code),
        PythonTracebackLexer(),
        HtmlFormatter(noclasses=True, linenos=linenos),
    )

    return formatted_code


def sentry_integrations():
    """
    Returns:
        list: integration frameworks to be used in our implementation of the
            Sentry SDK.
    """
    from sentry_sdk.integrations.argv import ArgvIntegration
    from sentry_sdk.integrations.atexit import AtexitIntegration
    from sentry_sdk.integrations.dedupe import DedupeIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.modules import ModulesIntegration
    from sentry_sdk.integrations.stdlib import StdlibIntegration

    return [
        ArgvIntegration(),
        AtexitIntegration(),
        DedupeIntegration(),
        LoggingIntegration(),
        ModulesIntegration(),
        StdlibIntegration(),
    ]


def sentry_before_send_callback(event, hint):
    """
    Executed before an event is sent to the Sentry server, gathers all error
    information and adds it to the event.

    Args:
        event (dict): Sentry event supplied before submission to server
        hint (dict): additional information, such as exc_info, log_record or
            httplib_request

    Returns:
        dict: modified Sentry event dictionary
    """
    info = all_information_by_section()
    user_info = info.pop("user")

    # add user data
    event_user = event.setdefault("user", dict())
    event_user.update(user_info)

    # add additional tags
    event_tags = event.setdefault("tags", dict())
    for section in info.values():
        event_tags.update(section)

    # add error reports
    event_extra = event.setdefault("extra", dict())
    error_reports = get_error_reports()
    if error_reports:
        event_extra["error_reports"] = error_reports

    return event


class ErrorEmail(object):
    """
    Error email generator and sender.

    Assembles a litney of relevant debug information for regarding the supplied
    exception event, then (via Jinja) produces valid HTML with inline CSS
    properties to email as desired.

    Args:
        exc_type (type): exception type class object
        exc_value (exception): class instance of exception parameter
        exc_traceback (traceback): encapsulation of call stack for exception
    """

    def __init__(self, exc_type, exc_value, exc_traceback):
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.exc_traceback = exc_traceback

        self.traceback_message = traceback.format_exception(
            self.exc_type, self.exc_value, self.exc_traceback
        )

        self.info = all_information_by_section()

    def sender(self):
        """
        The "from"-address for the error email.

        To circumvent Gmail's truncation of emails with a majority of content
        being identical, we append a unique identifier (in this case, a hashing of
        the error email's subject line) to the `thepipe@blur.com` address.

        Returns:
            str: unique "The Pipe" email address derived from subject
        """
        return blurdev.core.emailAddressMd5Hash(self.subject())

    def subject(self, max_length=150):
        """
        Error email subject line; includes several basic bits of information
        for quick identfication within ones Inbox.

        By default, subject is truncated to 150 characters. May be disabled by
        setting `max_length` to None.

        Args:
            max_length (int): maximum length for subject line; truncates string
                to `max_length - 3` and adds an ellipsis `...`

        Returns:
            str: email subject
        """
        tags = ""
        tag_keys = ["username", "core", "environment", "window.class"]
        for key in tag_keys:
            value = all_information().get(key, None)
            if value:
                tags += "[{label}:{value}]".format(label=key[0].upper(), value=value)

        subject = "[Python Error]{tags} {message}".format(
            tags=tags, message=self.traceback_message[-1].strip("\n")
        )

        # conditionally truncate subject length
        if isinstance(max_length, int) and max_length > 0:
            subject = "{subject:.{length}}{ellipsis}".format(
                subject=subject,
                length=max_length - 3,
                ellipsis="..." if len(subject) > max_length else "",
            )

        return subject

    def message(self):
        """
        Using a pre-made Jinja2 HTML template, render the contents of the
        error email.

        Returns:
            str: fully valid HTML output for error email with inline CSS
                properties
        """
        from jinja2 import Environment, PackageLoader

        # jinja environment to import template from resources directory and
        # add `highlight_code` to environment namespace for code-highlighting
        # process within the template
        jinja_env = Environment(loader=PackageLoader("blurdev", "resource"))
        jinja_env.globals["highlight_code"] = highlight_code

        template = jinja_env.get_template("error_mail_inline.html")
        render = template.render(
            subject=self.subject(max_length=None),
            info_dict=self.info,
            error_report=get_error_reports(),
            traceback=self.traceback_message,
            send_time=datetime.now().strftime("%b %d, %Y @ %I:%M %p"),
        )

        return render

    def send(self, recipients):
        """
        Initates sending of error email to supplied recipient list.

        Args:
            recipients (list): email addresses of recipients for error email
        """
        blurdev.core.sendEmail(
            self.sender(), recipients, self.subject(), self.message()
        )