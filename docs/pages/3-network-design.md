# Design Considerations

Before you install and run FakerNet, you need to consider how your environment will need to be structured to properly use FakerNet.

## The FakerNet Host

FakerNet is built to run on a single independent system, which we will call the FakerNet host. Systems that want to use the "internet" on the FakerNet host will need network access to the different networks that FakerNet will create. You have a couple of options to ensure hosts can reach all the networks that FakerNet will create.

### Gateway Method

The easiest method, and the recommended one, is to make the system the default gateway for the networks you want to connect to the fake internet. All hosts will sit behind the FakerNet host and route everything through it, including any access to the real internet. This strategy gives you the most control over access to the FakerNet systems and allows to you to redirect traffic to the FakerNet hosts. (This is especially useful to redirect DNS traffic.) Essentially, FakerNet works like your ISP.

### Side-load Method

Another method is utilize routing protocols to add the FakerNet networks to your existing routing infrastructure. You can use the Quagga that is installed for FakerNet or another method to add FakerNet's routes so that systems can access FakerNet systems. Setting up these routes goes beyond the realm of this documentation.

## DNS

To fully utilize FakerNet to its full advantage, you will need to have all your systems use the first FakerNet DNS server (called the primary DNS server) you will set up during on your first run. This means that either all hosts will have to use the primary FakerNet DNS server as its nameserver or use a server that does. If you have the FakerNet host as the default gateway, you can also use the ```redirect``` module to force all DNS queries to the FakerNet primary DNS server.

## Real Internet Access

Depending on your setup, you may or may not want access to real Internet resources in your environment. 

### No Internet

This can be simply done by using the Gateway method without connecting the FakerNet host to any further networks. The networking will end with the FakerNet host and all hosts in your environment will only have access to the FakerNet "internet."

### "Extended" Internet

This is using the Gateway method but also giving the FakerNet host a connection to the external network and the internet as a whole. You will need to configure NAT on the FakerNet host to enable proper routing to outside resources. Also configure your DNS server (especially your primary DNS server) with forwarders to resolve real internet names. Be aware that internal DNS schemes can be leaked by accident, so don't try using this scheme if you have sensitive DNS names.

Also, be careful of overriding existing domain names in your internal "internet" (unless that's your goal). Utilize root domains such as ```fake``` or ```test``` to host your services.  

In the end, your hosts will have access to the real internet alongside your FakerNet "internet."

### Proxied Internet

This is a mixture of the No Internet with the "Extended" Internet schemes. In this scheme, a proxy is configured with one interface on the internal FakerNet "internet" and one on the external network. This could be on a separate machine or, alongside iptables rules to block any other system from routing outside, on the FakerNet host itself. 

Hosts that you want the real internet on would be configured to use the proxy, while all other systems would use the FakerNet "internet" instead.

This scheme is not currently configured by FakerNet itself, so you're on your own in setting up as you see fit and what fits your needs.