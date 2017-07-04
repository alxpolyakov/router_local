from tik_local import settings
from dnslib.dns import RR, DNSRecord
from dnslib.server import DNSServer, DNSLogger
import threading

logger = DNSLogger()


class TestResolver:
    def resolve(self, request, handler):
        reply = request.reply()
        reply.add_answer(*RR.fromZone("%s. 60 A %s" % (settings.ROUTER_HOST, settings.WAN_IP,)))
        return reply

resolver = TestResolver()
server = DNSServer(resolver, port=8053, address="localhost", tcp=True, logger=logger)
server.start_thread()

q = DNSRecord.question("abc.com")

