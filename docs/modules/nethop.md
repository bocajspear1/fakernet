Nethop creates new networks and sets up a simple Alpine Linux router to act as its gateway. This allows for multi-tiered networks instead of just a flat one.

The router is a LXD container, not a Docker container, and runs Quagga that distributes routes currently by RIPv2.