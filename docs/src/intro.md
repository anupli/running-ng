# Introduction
`running-ng` is a collection of scripts that help people run workloads in a methodologically sound settings.

## Disclaimer
At this stage, the focus of this project is driven by the internal use of members from [Steve Blackburn](https://users.cecs.anu.edu.au/~steveb/)'s lab.
If you are a member of the lab, you know what to do if you encounter any issue, and you can ignore the below.

If you are a member of the public, please kindly note that the project is open-source and documented on a "good-faith" basis.
We might not have the time to consider your features requests.
Please don't be offended if we ignore these.
Having said that, you are very welcomed to use it, and we will be very pleased if this helps anyone.
In particular, we are grateful if you report bugs you found with steps to reproduce it.

## ⚠️ Warning
The syntax (of configuration files and command line arguments) of `running-ng` is not stabilized yet.
When you use it, expect breaking changes, although we will try to minimize this where possible.

`running-ng` has been tested by few people, and we think it is stable enough to use for your experiments.
However, there are probably few wrinkles to be ironed out.
Please file any bug or feature request on [the issue tracker](https://github.com/caizixian/running-ng/issues).

You are also welcome to implement new features and/or fix bugs by opening [pull requests](https://github.com/caizixian/running-ng/pulls).
But before you do so, please discuss with [Steve](https://github.com/steveblackburn) first for major design changes.
For non-user-facing changes, please discuss with the [maintainers](#maintainers) first.

## History
The predecessor of `running-ng` is `running`, a set of scripts written in Perl, dating back to 2005.
However, the type of workloads we are evaluation has changed a bit, and we want a new set of scripts that fit our needs better.

## Maintainers
- Zixian Cai
