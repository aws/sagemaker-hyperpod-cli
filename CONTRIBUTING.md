# Contributing Guidelines
Thank you for your interest in contributing to our project. Whether it's a bug report, new feature, correction, or additional
documentation, we greatly value feedback and contributions from our community.

Please read through this document before submitting any issues or pull requests to ensure we have all the necessary
information to effectively respond to your bug report or contribution.


## Reporting Bugs/Feature Requests
We welcome you to use the GitHub issue tracker to report bugs or suggest features.

When filing an issue, please check existing open, or recently closed, issues to make sure somebody else hasn't already
reported the issue. Please try to include as much information as you can. Details like these are incredibly useful:

* A reproducible test case or series of steps
* The version of our code being used
* Any modifications you've made relevant to the bug
* Anything unusual about your environment or deployment


## Contributing via Pull Requests
Contributions via pull requests are much appreciated. Before sending us a pull request, please ensure that:

1. You are working against the latest source on the *main* branch.
2. You check existing open, and recently merged, pull requests to make sure someone else hasn't addressed the problem already.
3. You open an issue to discuss any significant work - we would hate for your time to be wasted.

To send us a pull request, please:

1. Fork the repository.
2. Modify the source; please focus on the specific change you are contributing. If you also reformat all the code, it will be hard for us to focus on your change.
3. Ensure local tests pass.
4. Commit to your fork using clear commit messages. Also, you must [sign your commit using GPG](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification).
5. Send us a pull request, answering any default questions in the pull request interface.
6. Pay attention to any automated CI failures reported in the pull request, and stay involved in the conversation.

GitHub provides additional document on [forking a repository](https://help.github.com/articles/fork-a-repo/) and
[creating a pull request](https://help.github.com/articles/creating-a-pull-request/).


## Run the Unit Tests
Install tox using `pip install tox`
Run the following tox command and verify that all code checks and unit tests pass: `tox`. It will run test for Python 3.8, 3.9, 3.10, 3.11
You can also run a test suit with a single python version with the following command: `tox -e py311/py310/py39/py38`
You can also just run unit tests with command: `tox -e unit`


## Finding contributions to work on
Looking at the existing issues is a great way to find something to contribute on. As our projects, by default, use the default GitHub issue labels (enhancement/bug/duplicate/help wanted/invalid/question/wontfix), looking at any 'help wanted' issues is a great place to start.


## Code of Conduct
This project has adopted the [Amazon Open Source Code of Conduct](https://aws.github.io/code-of-conduct).
For more information see the [Code of Conduct FAQ](https://aws.github.io/code-of-conduct-faq) or contact
opensource-codeofconduct@amazon.com with any additional questions or comments.


## Security issue notifications
If you discover a potential security issue in this project we ask that you notify AWS/Amazon Security via our [vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/). Please do **not** create a public github issue.


## Licensing
See the [LICENSE](LICENSE) file for our project's licensing. We will ask you to confirm the licensing of your contribution.


## Troubleshooting
### pytest 'start_job' related Unit Test failures
- Underlying, the Click CLIRunner unit test tool has some issue with UTF-8 encoding
- To resolve this, temporary use ```LC_ALL=C pytest test/unit_tests``` to complete the Unit tests

### pytest 'NoSuchModule' errors
- double check whether ```pytest``` is running the same venv or global environment as your project by ```which pytest```.
- If ```pytest``` is running in venv, ensure ```hyperpod``` is installed in venv.
- Otherwise, if ```pytest``` is running globally, ensure ```hyperpod``` is installed globally.