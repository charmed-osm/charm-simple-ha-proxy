# charm-simple-ha-proxy

This is an example of a simple HA proxy charm used by Open Source Mano (OSM), written in the [Python Operator Framwork](https://github.com/canonical/operator)


## Usage

To get the charm:
```bash
git clone https://github.com/charmed-osm/charm-simple-ha-proxy
cd charm-simple-ha-proxy
# Install the submodules
git submodule update --init
```

To configure the charm, you'll need to have an SSH-accessible machine. You'll need the hostname, and the username and password to login to. Password authentication is useful for testing but key-based authentication is preferred when deploying through OSM.

To deploy to juju:
```
juju deploy . --config ssh-hostname=10.135.22.x --config ssh-username=ubuntu --config ssh-password=ubuntu
```

```
# Make sure the charm is in an Active state
juju status
```

To test the SSH credentials, run the `verify-ssh-credentials` action and inspect it's output:
```
$ juju run-action simple-ha-proxy/0 verify-ssh-credentials
Action queued with id: "9"

$ juju show-action-output 9
UnitId: simple-ha-proxy/0
results:
  Stdout: |
    Verified!
  verified: "True"
status: completed
timing:
  completed: 2020-02-14 19:30:38 +0000 UTC
  enqueued: 2020-02-14 19:30:33 +0000 UTC
  started: 2020-02-14 19:30:36 +0000 UTC
```

To exercise the charm, run the `touch` function

```bash
juju run-action simple-ha-proxy/0 touch filename=/home/ubuntu/firsttouch
```

Then ssh to the remote machine and verify that the file has been created.

### Scale

```bash
juju add-unit simple-ha-proxy --num-units 2
```