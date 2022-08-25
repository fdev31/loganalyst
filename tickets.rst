Tickets
=======

:total-count: 3

--------------------------------------------------------------------------------

Allow html output
=================

:bugid: 1
:created: 2022-08-25T00:10:18
:priority: 0

use different output objects (console is the default)

--------------------------------------------------------------------------------

Invalid event count
===================

:bugid: 2
:created: 2022-08-25T00:21:50
:priority: 0

Eg:
Summary for named identifier test (5/9)::

    933.000  IDPad systemd[767]: Started PipeWire PulseAudio. @ 2022-05-20 15:35:00+02:00
    933.000  IDPad systemd[767]: Started PipeWire Media Session Manager. @ 2022-05-20 15:35:00+02:00
    933.000  IDPad systemd[767]: Started PipeWire Multimedia Service. @ 2022-05-20 15:35:00+02:00
      0.000  IDPad systemd[767]: Started D-Bus User Message Bus. @ 2022-05-20 15:50:33+02:00

--------------------------------------------------------------------------------

Idea: support Events
====================

:bugid: 3
:created: 2022-08-25T20:07:38
:priority: 0

event=True

In this mode, end= is optional and events are just counted
. As a summary they would have statistics about event rates (eg: average, peak, ...)
