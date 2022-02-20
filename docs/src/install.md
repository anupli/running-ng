# Installation
`pip3 install --user -U running-ng`

The base configuration files can be usually be found in paths like `~/.local/lib/python3.6/site-packages/running/config/base`.
The exact path might differ depending on your Python version, etc.

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

To ensure `~/.bashrc` is always sourced, you can add the following to `~/.bash_profile`.
```bash
if [ -f ~/.bashrc ]; then
  . ~/.bashrc
fi
```

If you are a moma user, please change these dotfiles on `squirrel.moma`, and then run `sudo /moma-admin/config/update_self.fish`.
Note that you should run this command using a SSH session on a standard terminal instead of using the integrated terminal in VSCode Remote.
Please check [here](https://squirrel.anu.edu.au/#customization) for how to setup a UNIX password for `sudo`.
