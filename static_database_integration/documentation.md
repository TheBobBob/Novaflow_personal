# Static Database Integration for Static Databases 
In this folder, I will be working on integrating a static database into the agent. The two approaches I am considering now is having the database search built into the prompt, so there will be a preliminary layer before the final prompt. However, this is slightly slower because this creates another inference that we don't need. But it might be the only way because a rule-based approach won't work for how diverse it would need to be in the amount of prompts that might require a term search. 

For the preliminary layer approach, once we have multiple databases, we can integrate that all into the response and give it knowledge of the current contents in the database so that it can choose the entry that is semantically the closest? 

For this demo, I will integrate the GO terms database and Uniprot (in order to demo having multiple databases, each with only a few entries). At a more production level, we might want to start using the APIs, but some of these APIs are really slow, so manually transferring into a database or writing a script to do it might be best.


Proposed Steps: 
1. LLM gets a query 
2. Converts it to the data it needs and the database (if it needs to make multiple queries, put each on a newline and we will split it and check)
3. Makes the database query and returns the data (by default, it will have access to the columns, and will tell us what column we should go into to make the query)

