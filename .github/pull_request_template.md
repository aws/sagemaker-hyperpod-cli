# PR Approval Steps

## For Requester

1. Description
    - [ ] Check the PR title and description for clarity. It should describe the changes made and the reason behind them.
    - [ ] Ensure that the PR follows the contribution guidelines, if applicable.
2. Security requirements
    - [ ] Ensure that a Pull Request (PR) does not expose passwords and other sensitive information by using git-secrets and upload relevant evidence: https://github.com/awslabs/git-secrets
    - [ ] Ensure commit has GitHub Commit Signature
3. Manual review
    1. Click on the Files changed tab to see the code changes. Review the changes thoroughly:
        - [ ] Code Quality: Check for coding standards, naming conventions, and readability.
        - [ ] Functionality: Ensure that the changes meet the requirements and that all necessary code paths are tested.
        - [ ] Security: Check for any security issues or vulnerabilities.
        - [ ] Documentation: Confirm that any necessary documentation (code comments, README updates, etc.) has been updated.
4. Check for Merge Conflicts:
    - [ ] Verify if there are any merge conflicts with the base branch. GitHub will usually highlight this. If there are conflicts, you should resolve them.
      
## For Reviewer

1. Go through `For Requester` section to double check each item.
2. Request Changes or Approve the PR:
    1. If the PR is ready to be merged, click Review changes and select Approve.
    2. If changes are required, select Request changes and provide feedback. Be constructive and clear in your feedback.
3. Merging the PR
    1. Check the Merge Method:
        1. Decide on the appropriate merge method based on your repository's guidelines (e.g., Squash and merge, Rebase and merge, or Merge).
    2. Merge the PR:
        1. Click the Merge pull request button.
        2. Confirm the merge by clicking Confirm merge.

