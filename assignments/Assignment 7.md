# Question 1 (10 Points)

### Create a Pull Request and Create a Plan

Notes: To do it off the latest main branch use the following commands. You can also change main to another branch if you want to reuse previous work.
git checkout main
git pull
git checkout -b <branch>
<edit some file>
git add <file>
git commit -m “Homework assignment X”
git push origin <branch>
<Go to Github and be sure to create the PR>

Create a comment for your PR with a plan of action. Your plan of action should encompass how you plan to finish each of the other questions in this homework assignment. Do not edit this comment and it should be the first comment in the PR history.

Abraham Lincoln is often quoted as saying, “If I had eight hours to chop down a tree, I'd spend the first six hours sharpening my axe”. You will be graded based on the preparation and research you put into it. Your plan of action should be a short essay.

In your plan of action explain various approaches that you could take. Talk about their potential pros and cons. What alternatives did you consider to these decisions?

If it helps to think in these terms, this is essentially a mini-ADR (Architectural Decision Record).
Resource:
 
Template:
 

After creating the PR, since you haven’t made any major changes yet, you should see that the testing pipeline ran and passed at the bottom of the PR. After completing the assignment, you’ll need to ensure this is still green to get full points.


# Question 2 (5 Points)

## Host and serve your model through a Sagemaker endpoint, Bedrock, or locally

Resources:
Listing 6.3
 

Sagemaker

Bedrock
 

Open source:


 

# Question 3 (3 points)

## Send requests to your server programmatically

In src directory create a file named inference.py. Use python’s  package or the appropriate sagemaker/bedrock SDK to interact with your server. Take a screenshot showing your request and response with your API.

When you are done, format your code with .

Add and commit your code and push it to your PR.

***Ensure the CI test pipeline passes!***

# Question 4 (2 points)

## Explain your work

Review your PR. Add any helpful notes inline to your code explaining your work. In a comment be sure to explain how things went. Did things go as you initially planned?  Why or why not? 

Explain why you wrote the tests you did.

If you had more time, what would you do to improve this PR?

***Please remember to shut down your server if you deployed to a Sagemaker endpoint or other resource!***
