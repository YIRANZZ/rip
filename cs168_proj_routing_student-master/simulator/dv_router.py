"""
Your awesome Distance Vector router for CS 168

Based on skeleton code by:
  MurphyMc, zhangwen0411, lab352
"""

import sim.api as api
from cs168.dv import RoutePacket, \
                     Table, TableEntry, \
                     DVRouterBase, Ports, \
                     FOREVER, INFINITY

class DVRouter(DVRouterBase):

    # A route should time out after this interval
    ROUTE_TTL = 15

    # Dead entries should time out after this interval
    GARBAGE_TTL = 10

    # -----------------------------------------------
    # At most one of these should ever be on at once
    SPLIT_HORIZON = False
    POISON_REVERSE = False
    # -----------------------------------------------

    # Determines if you send poison for expired routes
    POISON_EXPIRED = False

    # Determines if you send updates when a link comes up
    SEND_ON_LINK_UP = False

    # Determines if you send poison when a link goes down
    POISON_ON_LINK_DOWN = False

    def __init__(self):
        """
        Called when the instance is initialized.
        DO NOT remove any existing code from this method.
        However, feel free to add to it for memory purposes in the final stage!
        """
        assert not (self.SPLIT_HORIZON and self.POISON_REVERSE), \
                    "Split horizon and poison reverse can't both be on"

        self.start_timer()  # Starts signaling the timer at correct rate.

        # Contains all current ports and their latencies.
        # See the write-up for documentation.
        self.ports = Ports()

        # This is the table that contains all current routes
        self.table = Table()
        self.table.owner = self

        self.history = {}


    def add_static_route(self, host, port):
        """
        Adds a static route to this router's table.

        Called automatically by the framework whenever a host is connected
        to this router.

        :param host: the host.
        :param port: the port that the host is attached to.
        :returns: nothing.
        """
        # `port` should have been added to `peer_tables` by `handle_link_up`
        # when the link came up.
        assert port in self.ports.get_all_ports(), "Link should be up, but is not."

        # TODO: fill this in!

        self.table[host] = TableEntry(dst=host, port=port, latency=self.ports.get_latency(port), expire_time=FOREVER)


    def handle_data_packet(self, packet, in_port):
        """
        Called when a data packet arrives at this router.

        You may want to forward the packet, drop the packet, etc. here.

        :param packet: the packet that arrived.
        :param in_port: the port from which the packet arrived.
        :return: nothing.
        """
        # TODO: fill this in!

        if packet.dst in self.table and self.table[packet.dst][2] < INFINITY:
            self.send(packet, self.table[packet.dst][1])

    def send_routes(self, force=False, single_port=None):
        """
        Send route advertisements for all routes in the table.

        :param force: if True, advertises ALL routes in the table;
                      otherwise, advertises only those routes that have
                      changed since the last advertisement.
               single_port: if not None, sends updates only to that port; to
                            be used in conjunction with handle_link_up.
        :return: nothing.
        """
        # TODO: fill this in!

        # self.table[host] = TableEntry(dst=host, port=port,
        #                              latency=self.ports.get_latency(port), expire_time=FOREVER)

        # Split Horizon a->b->c don't advertise destination c to neighbor b

        if single_port == None:
            for port in self.ports.get_all_ports():
                for entry in self.table.values():
                    dst = entry[0]
                    latency = entry[2]
                    neighbor = entry[1]
                    # 如果要通过port到host，把那个host的路由项设成INDINITY发给这个neighbor
                    if (self.POISON_REVERSE and port == neighbor):
                        packet = RoutePacket(dst, INFINITY)
                        if force == True:
                            self.send(packet, port)
                            self.update_history(port, packet)
                        elif self.has_no_updated(port, packet):
                            self.send(packet, port)
                            self.update_history(port, packet)
                    #不发给这个neighbor
                    elif self.SPLIT_HORIZON and port == neighbor:
                        pass
                    else:
                        packet = RoutePacket(dst, latency)
                        if (force == True):
                            self.send(packet, port)
                            self.update_history(port, packet)
                        elif self.has_no_updated(port, packet):
                            self.send(packet, port)
                            self.update_history(port, packet)

        else:
            port = single_port
            for entry in self.table.values():
                dst = entry[0]
                latency = entry[2]
                neighbor = entry[1]
                # 如果要通过port到host，把那个host的路由项设成INDINITY发给这个neighbor
                if (self.POISON_REVERSE and port == neighbor):
                    packet = RoutePacket(dst, INFINITY)
                    if force == True:
                        self.send(packet, port)
                        self.update_history(port, packet)
                    elif self.has_no_updated(port, packet):
                        self.send(packet, port)
                        self.update_history(port, packet)
                # 不发给这个neighbor
                elif self.SPLIT_HORIZON and port == neighbor:
                    pass
                else:
                    packet = RoutePacket(dst, latency)
                    if (force == True):
                        self.send(packet, port)
                        self.update_history(port, packet)
                    elif self.has_no_updated(port, packet):
                        self.send(packet, port)
                        self.update_history(port, packet)


    def expire_routes(self):
        """
        Clears out expired routes from table.
        accordingly.
        """
        # TODO: fill this in!

        """
          A routing table

          You should use a `Table` instance as a `dict` that maps a
          destination host to a `TableEntry` object.
        """

        # usr list in order to keep keys to be deleted  are correct
        for key in list(self.table.keys()):
            if self.table[key].has_expired:
                if self.POISON_EXPIRED:
                    self.table[key] = TableEntry(self.table[key][0], self.table[key][1], INFINITY, api.current_time() + self.ROUTE_TTL)
                else:
                    del self.table[key]


    def handle_route_advertisement(self, route_dst, route_latency, port):
        """
        Called when the router receives a route advertisement from a neighbor.

        :param route_dst: the destination of the advertised route.
        :param route_latency: latency from the neighbor to the destination.
        :param port: the port that the advertisement arrived on.
        :return: nothing.
        """
        # TODO: fill this in!

        # self.table[host] = TableEntry(dst=host, port=port,
        #                             latency=self.ports.get_latency(port), expire_time=FOREVER)

        if route_dst in self.table:
            if route_latency >= INFINITY:
                if self.table[route_dst][1] == port and self.table[route_dst][2] < INFINITY:
                    self.table[route_dst] = TableEntry(route_dst, port, INFINITY,
                                                       self.table[route_dst][3])

            else:
                if self.table[route_dst][2] > route_latency + self.ports.get_latency(port):
                    self.table[route_dst] = TableEntry(route_dst, port, route_latency + self.ports.get_latency(port), api.current_time() + self.ROUTE_TTL)
                if self.table[route_dst][1] == port:
                    self.table[route_dst] = TableEntry(route_dst, port, route_latency + self.ports.get_latency(port),
                                                       api.current_time() + self.ROUTE_TTL)
        else:
            self.table[route_dst] = TableEntry(route_dst, port, route_latency + self.ports.get_latency(port),
                                               api.current_time() + self.ROUTE_TTL)

        self.send_routes()


    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this router goes up.

        :param port: the port that the link is attached to.
        :param latency: the link latency.
        :returns: nothing.
        """
        self.ports.add_port(port, latency)

        # TODO: fill in the rest!

        if self.SEND_ON_LINK_UP:
            self.send_routes(True, port)

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this router does down.

        :param port: the port number used by the link.
        :returns: nothing.
        """
        self.ports.remove_port(port)

        # TODO: fill this in!

        if self.POISON_ON_LINK_DOWN:
            for key in list(self.table.keys()):
                if self.table[key][1] == port:
                    # time should ROUTE_TTL or maintain?
                    self.table[key] = TableEntry(self.table[key][0], self.table[key][1], INFINITY, api.current_time() + self.ROUTE_TTL)

            self.send_routes()

    # Feel free to add any helper methods!

    def update_history(self, port, packet):
        self.history[(port, packet.destination)] = packet.latency

    def has_no_updated(self, port, packet):
        if (port, packet.destination) in self.history.keys() and self.history[(port, packet.destination)] == packet.latency:
            return False
        else:
            return True

