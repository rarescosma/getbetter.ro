Title: Making traffic to co-located OpenVPN services appear local

### The Problem

Say we have a good old OpenVPN configuration between a client and a server.

The server also hosts a bunch of other services, perhaps it has a local Kubernetes cluster, and perhaps some of the services on this cluster are sensitive and should only be accessible locally.

!!! help "Kubernetes Parenthesis"

    Breaking scope here a bit, but if you _were_ to restrict a Kubernetes nginx ingress to only accept local traffic you would do so via the following annotation:

    ```
    metadata:
        annotations:
            nginx.ingress.kubernetes.io/whitelist-source-range: 127.0.0.0/24,172.16.0.0/16,10.0.0.0/8
    ```

By default, when the OpenVPN tunnel is established, the client gets a couple of new IP routes that tell it to forward all traffic through the tunnel, _except_ for traffic going to the server's public IP address. 

This avoids a chicken and egg problem: the tunnel itself is nothing but an encrypted connection that needs to happen over the public Internet.

Let's say the server's public IP is `1.2.3.4`. Looking through the routing table, we'd see something similar to this:

```
ip route | grep -E '0.0.0.0|1.2.3.4'

  0.0.0.0/1 via 172.16.16.5 dev tun0
  1.2.3.4 via <gateway_ip> dev eth0 
```

Which means any traffic towards the OpenVPN-hosting server, regardless if it's for other services, will appear as originating from the server's public IP (the public Internet), instead of appearing local. The example ingress config from above would gladly reject it with a `403`.

So we've got more chicken than eggs: the routing table should be smarter than this and only send traffic meant for the OpenVPN port through the public Internet and everything else through the tunnel. Unfortunately, OpenVPN is not sophisticated enough to make this happen.

So how can we fix this?

### The Solution

The easy answer is: switch to [Wireguard](https://www.wireguard.com/quickstart/), as it's configured by default to send traffic meant for other co-located services on the VPN server _through_ the tunnel.

But that's not why we're here, so to fix it while still using OpenVPN we'll need to:

1. Add a dummy interface on the server and assign it a [local IP address](https://www.rfc-editor.org/rfc/rfc1918)
1. Let the OpenVPN clients know how to reach the dummy IP address
1. Use a [DNAT + SNAT](https://en.wikipedia.org/wiki/Network_address_translation) combo to "hijack" traffic from the client that would go over the public Internet to the server's public IP and send it through the tunnel

Let's go through this step by step.

#### 1. Adding a dummy interface with a private IP on the server

First, pick a private IP subnet that doesn't conflict with any other subnets (like the ones used by the OpenVPN setup). For example, we'll use `172.16.100.100`.

Run the following in a shell _on the server_:

```shell
# (on the server)

sudo ip link add private0 type dummy
sudo ip address add 172.16.100.100 dev private0
```

#### 2. Let the OpenVPN clients know how to reach the new private IP

Edit the OpenVPN server configuration and make it push a route to all connecting clients that will configure them to route traffic destined for the private IP through the tunnel.

Add this to the servers OpenVPN config file (usually `/etc/openvpn/server.conf`):

```
push "route 172.16.100.0 255.255.255.0"
```

Make sure to restart the OpenVPN server.

#### 3. Set up NAT on the client to "hijack" non-OpenVPN traffic destined for the server and send it through the tunnel

We'll use OpenVPN's support for `up` and `down` scripts to achieve this.

```shell
cat > openvpn-up.sh <<EOF
#!/bin/bash

DUMMY_IP="172.16.100.100"

iptables -t nat -A OUTPUT -d "${trusted_ip}/32" -p tcp -j DNAT --to-destination "${DUMMY_IP}" \
    -m comment --comment "openvpn-up marker"
iptables -t nat -A POSTROUTING -d "${DUMMY_IP}/32" -p tcp -m tcp -j SNAT --to-source "${ifconfig_local}" \
    -m comment --comment "openvpn-up marker"

EOF

chmod +x openvpn-up.sh
```

This will have 2 effects:

- packages whose __destination IP__ is set to the servers __public IP__ (provided by the OpenVPN client through the `${trusted_ip}` variable) will have their __destination IP__ rewritten to the __dummy private IP__ we've set up in [step 1](#1-adding-a-dummy-interface-with-a-private-ip-on-the-server)
- packages whose __source IP__ is set to the client's __local IP__ and whose __destination IP__ is the __dummy IP__ will have their __source IP__ rewritten to the __private IP__ corresponding to the client's end of the OpenVPN tunnel (confusingly, this is provided by the OpenVPN client through a variable named `${ifconfig_local}`)

The net effect is that __all__ TCP traffic that would've been sent over the public Internet to the server's public IP will be routed _through the tunnel_ instead.

!!! warning

    We're making a couple of assumptions here:

    1. OpenVPN is set up to use the `UDP` protocol. If your specific setup uses `TCP` you'll have to adjust the iptables rules to _exclude_ traffic going to the OpenVPN TCP port.
    2. We're only interested in `TCP` traffic. If you want to give `UDP` traffic the same treatment you'll need a couple of additional iptables rules with `-p udp` instead of `-p tcp`.


We'll also set up a clean-up script to delete any rules that have the `openvpn-up` marker we've used. This script will be run whenever the OpenVPN tunnel goes down.

```shell
cat > openvpn-down.sh <<EOF
#!/bin/bash

iptables-save | grep "openvpn-up marker" \
    | cut -d" " -f2- \
    | sed 's#^#iptables -t nat -D #' \
    | paste -sd";" | bash

EOF

chmod +x openvpn-down.sh
```

Finally, we'll need to edit the client's OpenVPN configuration file to wire the custom scripts in.

Add the following to the clients OpenVPN config file:

```
script-security 2
up "/absolute/path/to/openvpn-up.sh"
down "/absolute/path/to/openvpn-down.sh"
```

Don't forget to replace the paths with the correct ones.

Restart the OpenVPN client and enjoy. 

!!! info
 
    Check out [this short guide](https://www.geeksforgeeks.org/difference-between-snat-and-dnat/) for more information about Source and Destination Network Address Translation (SNAT & DNAT).

That's all folks, keep encrypting! 🔒
