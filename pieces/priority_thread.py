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
#   The Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor
#   Boston, MA  02110-1301, USA.
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

__target_priority = 6
__highest_priority = 7

# Could also be a function of the number of seeders and/or block size
# Or more flexibly, this could be hooked up to a UI component.
__high_pri_queue_size = 10
__high_pri_queues = {}
# Store the original priorities so we can reset if something changes.
__high_pri_old_priorities = {}

def priority_loop(get_torrents_func, get_download_counts_func):
    torrents = get_torrents_func()
    download_counts = get_download_counts_func()
    for t in torrents:
        tor = component.get("TorrentManager").torrents.get(t)
        if not tor:
          continue
        if tor.status.state == tor.status.downloading:
            old_piece_queue = __high_pri_queues.get(t)
            num_pieces = download_counts.get(t)
            if not t:
              num_pieces = __high_pri_queue_size
            new_piece_queue = get_piece_queue(tor, num_pieces)

            # If there was an old queue, and the new one is different, reset old priorities
            # before proceeding. This will happen often, but this is cheap, and avoids cases
            # where something earlier that was previously 'do not downloaded' is requested.
            if old_piece_queue is not None and old_piece_queue != new_piece_queue:
              old_priorities = __high_pri_old_priorities[t]
              if old_priorities is not None and len(old_priorities) == len(old_piece_queue):
                for piece_index, old_priority in zip(old_piece_queue, old_priorities):
                  tor.handle.piece_priority(piece_index, old_priority)

            if old_piece_queue is None or old_piece_queue != new_piece_queue:
              # Store the original priorities before making modifications
              original_priorities = [tor.handle.piece_priority(i) for i in new_piece_queue]

              if len(new_piece_queue) > 0:
                # Set the first piece to highest priority
                tor.handle.piece_priority(new_piece_queue[0], __highest_priority)

                # Set the rest of the queue to second highest priority
                for i, piece_index in enumerate(new_piece_queue[1:]):
                  if (original_priorities[i] < __target_priority):
                    tor.handle.piece_priority(piece_index, __target_priority)

              # Finally store the new queue state for the next interation
              __high_pri_old_priorities[t] = original_priorities
              __high_pri_queues[t] = new_piece_queue

def get_piece_queue(torrent, max_num_pieces):
  # First go backwards from the first queued piece to make sure everything
  # before it has been downloaded that needs to be.
  new_queue = []
  try:
    next_undownloaded = -1
    pieces = torrent.status.pieces
    priorities = torrent.handle.piece_priorities()
    while len(new_queue) < max_num_pieces:
      next_undownloaded = pieces.index(False, next_undownloaded + 1)
      while priorities[next_undownloaded] == 0:
        next_undownloaded = pieces.index(False, next_undownloaded + 1)
      new_queue.append(next_undownloaded)
  except ValueError:
    pass
  return new_queue
