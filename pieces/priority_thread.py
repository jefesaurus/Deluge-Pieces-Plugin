#
# priority_thread.py
#
# Copyright (C) 2010 Nick Lanham <nick@afternight.org>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.

from deluge.ui.client import client
import deluge.component as component

__target_priority = 5

# Could also be a function of the number of seeders
__high_pri_queue_size = 10
__high_pri_queues = {}

def priority_loop(meth):
    torrents = meth()
    for t in torrents:
        tor = component.get("TorrentManager").torrents[t]
        if tor.status.state == tor.status.downloading:
            piece_queue = __high_pri_queues.get(t)
            if not(piece_queue):
                piece_queue = []
            # Filter out already downloaded pieces
            piece_queue = [x for x in piece_queue if not tor.status.pieces[x]]
            priorities = tor.handle.piece_priorities()

            while len(piece_queue) < __high_pri_queue_size:
                if len(piece_queue) == 0:
                    next_possibility = 0
                else:
                    next_possibility = piece_queue[-1] + 1
                try:
                    next = tor.status.pieces.index(False, next_possibility)
                    if (priorities[next] == 0):
                        while (priorities[next] == 0):
                            next += 1
                            pcand = 0
                            for (i,x) in enumerate(priorities[next:]):
                                if x > 0:
                                    pcand = i + next
                                    break
                            next = max(tor.status.pieces.index(False,next), pcand)
                    piece_queue.append(next)
                except ValueError:
                    break
            
            for piece_index in piece_queue:
                if (priorities[piece_index] < __target_priority):
                  tor.handle.piece_priority(piece_index, __target_priority)
            __high_pri_queues[t] = piece_queue
