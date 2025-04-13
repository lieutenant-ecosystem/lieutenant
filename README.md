# What is Lieutenant?

Lieutenant, inspired by Microsoft's "Copilot," is an ecosystem that seamlessly connects your systems with large language models, empowering everyone with artificial intelligence.

The technical documentation is [here](https://lieutenant-ecosystem.github.io/).

# How to run the development environment

1. Fork [this](https://github.com/lieutenant-ecosystem/lieutenant.git) GitHub repository.
2. Clone the forked repository.
3. Run the following script:

```bash
#!/bin/bash

git remote add upstream https://github.com/lieutenant-ecosystem/lieutenant.git    # Adds the upstream branch
git fetch upstream                                                                # Fetch Changes from the upstream branch
git checkout main                                                                 # Switch the main branch
git merge upstream/main                                                           # Merge the changes from the upstream branch into your local branch
git push origin main                                                              # Push the updated branch to Your fork
```

# How to start up the development environment's infrastructure
1. Set all the environmental variables into a file called `.env_local`.
2. Execute the `dev/deploy.sh` script