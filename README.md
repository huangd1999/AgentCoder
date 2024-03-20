To execute AgentCoder, you should have API key from OpenAI or other similar third-party. AgentCoder is done with AIOHUB (https://api.aiohub.org/) since it provide funding for AgentCoder.

You should add you API key in agent_1 and agent_2 py file.

```
openai.api_base = "https://api.aiohub.org/v1"
openai.api_key = 'API Here'
```

Then, for code generation, you can just directly run the code with:
```
python programmer_humaneval.py
python programmer_mbpp.py
```
to generate code that will be used to assistant test case generation.

Then test case generation:
```
python test_designer.py
```

Finally, self-optimization process:

```
python test_executor_humaneval.py
python test_executor_mbpp.py
```

Since MBPP's format have few difference with HumanEval.
So for agent_1 and agent_3 we provide another files for execution. While agent_2 is same as HumanEval