# Question 1 (4 points)

## Create a PR to the class’s GitHub repo.

Notes: To do it off the latest main branch use the following commands. For this assignment however, you’ll want to base it off your previous homework branch. 
git checkout main
git pull
git checkout -b <branch>
<edit some file>
git add <file>
git commit -m “Homework assignment X”
git push origin <branch>
<Go to Github and be sure to create the PR>

Create a comment for your PR with a plan of action. Your plan of action should encompass how you plan to finish each of the other questions in this homework assignment. Do not edit this comment and it should be the first comment in the PR history.

Abraham Lincoln is often quoted as saying, “If I had eight hours to chop down a tree, I'd spend the first six hours sharpening my axe”. You will be graded based on the preparation and research you put into your plan. It should essentially be a short essay.

In your plan of action explain various approaches that you could take. Talk about their potential pros and cons. What alternatives did you consider to these decisions?

If it helps to think in these terms, this is essentially a mini-ADR (Architectural Decision Record).
Resource:
 
Template:
 

After creating the PR, since you haven’t made any major changes yet, you should see that the testing pipeline ran and passed at the bottom of the PR. After completing the assignment, you’ll need to ensure this is still green to get full points.


# Question 2 (3 points) 

## Build a Better Tokenizer

Some resources you might want to check out while working on this assignment:
Chapter 4 Section 4.4.1

Huggingface’s excellent summary of tokenizers:
 

Starting with the basic tokenizer you built in the last assignment, extend it to be a better tokenizer. This is an open ended question. Improve the tokenizer implementation in whatever direction you see fit.

Here is an example of how you might improve this tokenizer, using the BPE tokenization methodology talked about in the summary above.
 

# Question 3 (2 points)

## Write tests and format your code

Using  write as many tests as needed to show your Tokenizer is working as intended.

When you are done, format your code with .

Add and commit your code and push it to your PR.

***Ensure the CI test pipeline passes!***
# Question 4 (1 point)

Review your PR. Add any notes to your code.

Explain in your own words why the tokenizer you made is better than the SimpleTokenizer class I gave you.

Please share how things went. Did things go as you initially planned?  Why or why not? 

Explain why you wrote the tests you did.

If you had more time, what would you do to improve this PR?
