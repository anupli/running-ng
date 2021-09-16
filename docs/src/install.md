# Installation
For now, the best way to install `running-ng` is via source.
```bash
git clone https://github.com/anupli/running-ng
cd running-ng
pip3 install -e . --user
```

The `-e` option is used to allow quick update of `running-ng` by running `git pull`.
Once the codebase is more stabilized, other installation options, such as installing from PyPI, could be preferable.

## Adding `running` to `PATH`
You will need to add the folder where `running` is installed to your `PATH`.
On a typical Linux installation, `running` is installed to `~/.local/bin`.

You will need to refer to the documentation of the shell you are using.

Here is an example for bash.
```bash
# Add the following to ~/.bashrc
PATH=$PATH:$HOME/.local/bin
```
You don't need to use `export`.
Generally, `$PATH` already exists and is exported to child processes.

Please check whether your `~/.bash_profile` or `~/.profile` `source`s `~/.bashrc`.
If not, when you use a login shell (e.g., in the case of tmux), the content of `~/.bashrc` might not be applied.

To ensure `~/.bashrc` is always sourced, you can write add the following to `~/.bash_profile`.
```bash
if [ -f ~/.bashrc ]; then
  . ~/.bashrc
fi
```

If you are a moma user, please change these dotfiles on `squirrel.moma`, and then run `sudo /moma-admin/config/update_self.fish`.
Please check [here](https://squirrel.anu.edu.au/#customization) for how to setup a UNIX password for `sudo`.
