## Whirlwind

Proactive change agent for services managed by Juju

### Features

To experiment with proactive change of services, this tool watches a Juju deployment and performs unit replacement. Units for working services get replaced every 10 minutes, by default. The replacement interval, as well as the watched services, are configurable by the end user.

In the future, this tool should be able to properly hook into Juju to track convergence of changes across services, as well as provide other forms of proactive change (switching charms, service configuration, constraints, etc.)

### Concepts

Juju provides a solid model for describing services and relationships, along with the orchestration needed to deploy those services. It provides a number of features that can be used to perform proactive changes for an application stack.

- `juju add-unit <service>` and `julu remove-unit <unit>` provide the ability to [scale and replace service units](https://juju.ubuntu.com/docs/charms-scaling.html)
- `juju upgrade-charm --switch <charm> <service>` provides the ability to [switch out service implementations](https://juju.ubuntu.com/docs/authors-charm-upgrades.html)
- `juju quickstart <bundle>` provides the ability to [deploy a set of services](https://juju.ubuntu.com/docs/charms-bundles.html)
- `juju set <service> <options>` provides the ability to [change service configuration](https://juju.ubuntu.com/docs/charms-config.html)
- `juju set-constraints --service <service> <options>` provides the ability to [change service constraints for new machines](https://juju.ubuntu.com/docs/charms-constraints.html)

Juju also provides functionality similar to Fabric or MCollective, like the ability to [execute commands or distribute files](https://juju.ubuntu.com/docs/charms-working-with-units.html) to multiple machines.

### Development

1. Deploy Juju
2. Clone this repository
3. Install dependencies with `pip install -r requirements.txt`
4. Customize the example configuration file for your environment
5. Start the agent with `python whirlwind.py -v`

Some of this process can be expedited using `vagrant up` with the included `Vagrantfile`.

### Resources

- [Getting Started with Juju] (https://juju.ubuntu.com/docs/getting-started.html)
- [Manage Juju with the GUI] (https://juju.ubuntu.com/docs/howto-gui-management.html)
