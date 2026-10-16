Foundations of Generative AI and Prompt Engineering
Course Introduction 
This course focuses on practical skills for creating intelligent, dynamic AI-driven solutions, serving as an introduction to generative AI application development.
Foundations of Generative AI & Prompt Engineering
Grasp fundamental generative AI principles and learn how prompt engineering optimizes AI interactions.
Master key prompting techniques—including chain-of-thought and in-context learning—to craft robust prompt templates.
LangChain Framework & Application Development
Utilize the LangChain framework to construct versatile, context-aware AI applications leveraging tools, chains, and agents.
Participate in practical labs to construct prompt templates and embed sophisticated AI functionality into applications.
Building GenAI Web Applications
Combine LangChain with Flask to construct interactive, real-time generative AI web applications.
Assess and compare various language models to identify the most suitable option for specific use cases and maximize performance.
Suggested Follow-Up Questions
What role does the LangChain framework play in generative AI application development?
How can a prompt template be constructed using LangChain?
What process should be used to compare language models for a GenAI web app?
RAG and Agentic AI Professional Certificate Overview
​Retrieval Augmented Generation (RAG) integrates real-time information retrieval to deliver accurate, context-aware AI responses.
Multimodal AI enables processing and integrating diverse data types, including text, images, audio, and video.
Agentic AI empowers systems to reason, plan, and autonomously execute tasks.
The program consists of eight independent short courses (each 2–3 modules) with hands-on labs, projects, and graded quizzes leading to an IBM completion certificate:
Course 1: Generative AI Applications – Basics of GenAI, prompt engineering, in-context learning, prompt templates, and the LangChain framework.
Course 2: RAG Applications – Core RAG components, implementation using LangChain, UI setup with Gradio, and bot creation with LlamaIndex and IBM Granite.
Course 3: Vector Databases for RAG – ChromaDB architecture, vector operations, similarity search, and building a recommendation system.
Course 4: Advanced RAG with Vector Databases and Retrievers – Advanced retrieval patterns, FAISS integration, and RAG application development.
Course 5: Multimodal Generative AI Applications – Speech recognition, text-to-speech, computer vision, OpenAI Whisper, Mistral, image generation, captioning, and cross-modal retrieval.
Course 6: AI Agents – Function calling, tool orchestration, manual output parsing, and built-in LangChain agents (DataFrame and SQL).
Course 7: Agentic AI Fundamentals with LangChain and LangGraph – Stateful workflows, ReAct agents, multi-agent system design, and agentic RAG.
Course 8: Agentic AI with LangGraph, CrewAI, AG2 (AutoGen), and BAI Framework – State-of-the-art design patterns, multi-agent orchestration, and conversation-driven systems.
Course Overview
Warning: 8 XP • Prototyping and Strategic Evaluation of Generative AI
8 XP • Prototyping and Strategic Evaluation of Generative AI
0:12/4:25
Hello, and welcome to the Develop Generative AI Applications: Get Started course.
This course is designed for aspiring AI developers, machine learning engineers, data scientists, and AI researchers. It equips you with the knowledge and skills to develop and integrate generative AI solutions. You'll explore core prompt engineering techniques, such as in-context learning, and learn to create and manage prompt templates using frameworks like LangChain.
As you progress, you'll master key LangChain concepts, including chains, tools, and agents, to build smarter AI applications. Through hands-on labs, you'll experiment with AI model configurations and develop functional AI-powered applications. By the end, you'll have the expertise to design and implement generative AI solutions effectively.
This course is part of the IBM RAG and Agentic AI Professional Certificate, designed to provide you with the practical skills and knowledge to excel in developing advanced AI applications that leverage retrieval-augmented generation (RAG), multimodal AI, and agentic AI systems.
Prerequisites
Python programming skills and experience are required, as the course emphasizes coding and application development. Additionally, fundamental knowledge of AI and web development is highly recommended. A strong foundation in generative AI is recommended but not required.
Objectives
After completing this course, you will be able to:
Examine foundational concepts of generative AI and the LangChain framework, focusing on how prompt engineering and in-context learning enhance AI interactions
Apply prompt templates, chains, and agents to create flexible and context-aware AI applications using LangChain's modular approach
Develop a generative AI web application with Flask, integrating advanced features such as JSON output parsing for structured AI responses
Evaluate and compare different language models to select the most suitable option for specific use cases, ensuring optimal performance and reliability
Course Outline
This course consists of three modules.
Module 1: Foundations of Generative AI and Prompt Engineering
Lesson 0: Welcome
Lesson 1 [Optional]: Introduction to Generative AI
Lesson 2: Working with Prompt Engineering and Prompt Templates
Lesson 3: Module Summary and Evaluation
Key Topics:
Generative AI Models
NLP (Natural Language Processing)
Prompt Engineering and In-Context Learning
Advanced Methods of Prompt Engineering
LangChain LCEL Chaining Method
LangChain Prompt Templates
Module 2: Introduction to LangChain in GenAI Applications
Lesson 1: LangChain Core Components and Advanced Features
Lesson 2: Module Summary and Evaluation
Key Topics:
LangChain: Core Concepts
LangChain Advanced Features: Chains and Agents
Build Smarter AI Apps: Empower LLMs with LangChain
Module 3: Build a Generative AI Application with LangChain
Lesson 1: Application Development Workflow with Generative AI
Lesson 2: Module Summary and Evaluation
Lesson 3: Course Wrap-Up
Key Topics:
Choose the Right AI Model for Your Use Case
From Idea to AI: Building Applications with Generative AI
Python with Flask for Large-Scale Projects
Hands-on with GenAI: Choosing the Right Model for Your Application
Tools/Software
In this course, you will explore and utilize a variety of tools and platforms, including:
LangChain to design and implement structured AI workflows, integrate LLMs with external data sources, and optimize prompt engineering techniques
Flask, HTML5 and CSS3 to develop AI-powered web applications with interactive features
LangChain's JsonOutputParser to generate structured JSON outputs from LLM responses for enhanced data usability
LLMs (Llama 3, Granite, Mixtral) to experiment with different AI models, compare their performance, and select the best fit for specific applications
Python for coding AI applications, integrating APIs, and implementing LangChain's functionalities effectively
Tips for Success
Stay organized and track key program milestones, risks, and stakeholder communications
Consistently practice using the generative AI tools and techniques covered in the course
Congratulations on taking this step to elevate your career with generative AI! Enjoy your learning journey.


Generative AI Essentials
Introduction to Generative AI
​Welcome to Introduction to Generative AI. ​After watching this video, you'll be able to describe generative AI and its evolution. ​You'll also be able to explain how generative AI differs from discriminative AI. ​Artificial intelligence or AI has been around for years, shaping almost every sphere of ​our lives and revolutionizing how we live and work. ​At its core, AI can be defined as the simulation of human intelligence by machines. ​AI models learn from vast amounts of existing data. ​The process of learning from data is called training. 
​There are two fundamental approaches to AI, discriminative AI and generative AI. ​Discriminative AI is an approach that learns to distinguish between different classes of ​data. ​A discriminative AI model is given a set of training data, where each data point is labeled ​with its class. ​The model then predicts the class of a new data point by finding the side of the decision ​boundary that the data point falls on. ​Discriminative AI models use advanced algorithms to differentiate, classify, identify patterns ​and draw conclusions based on training data. ​One example of how a discriminative AI model works can be seen in how email spam filters ​can differentiate between spam and non-spam emails. ​Discriminative AI models are best applied to classification tasks. 
​They cannot, however, understand context or generate new content based on a contextual ​understanding of the training data. ​This is where generative artificial intelligence, or generative AI, comes in. ​Generative AI models learn to generate new content based on the training data. ​They can capture the underlining distribution of the training data and generate novel data ​instances. ​Generative AI starts with a prompt. ​This can be text, an image, video or any other input that the model can process. ​As an output, the model generates new content including text, images, audio, video, code ​and data. 
​Generative AI can produce output in the same form in which the prompt is provided. ​For example, text-to-text or in a different form from the prompt such as text-to-image ​or image-to-video. ​Here is a simple example to understand the difference between discriminative or traditional ​AI and generative AI. ​Discriminative AI would be best suited to answer questions such as, is this image a ​drawing of a nest or an egg? ​Generative AI would respond to prompts such as draw an image of a nest with three eggs ​in it. ​While discriminative AI mimics our analytical and predictive skills, generative AI goes ​a step further to mimic our creative skills. ​As implied by this comment from the Harvard Business Review, "AI can not only boost our ​analytic and decision-making abilities but also heighten creativity." 
​Generative models can take what they have learned and create entirely new content based ​on that information. ​Both discriminative and generative models are created using deep learning techniques. ​Deep learning involves training artificial neural networks to learn from vast amounts ​of data. ​An artificial neural network is a collection of smaller computing units called neurons, ​which are modeled in a manner that is similar to how a human brain processes information. ​The creative skills of generative AI come from generative AI models such as generative ​adversarial networks or GANs, variational autoencoders or VAEs, transformers, and diffusion ​models. ​These models can be considered as the building blocks of generative AI. ​Generative AI is not a new concept. 
​Its roots trace back to the origins of machine learning. ​In the late 1950s, when scientists proposed machine learning, they explored using algorithms ​to create new data. ​During the 1990s, the rise of neural networks infused advancements in generative AI. ​Further, during the early 2010s, deep learning, supported by the availability of large data ​sets and enhanced computing power, further advanced the development of generative AI. ​In 2014, generative AI was transformed with the introduction of GANs by Ian Goodfellow ​and his colleagues. ​GANs and other models such as VAEs and transformers set the stage for generative AI's growth ​and the development of foundational models and tools. ​Foundation models are AI models with broad capabilities that can be adapted to create ​more specialized models or tools for specific use cases. 
​A specific category of foundation models, called large language models or LLMs, are ​trained to understand human language and can process and generate text. ​In 2018, OpenAI introduced a transformer-based LLM called Generative Pre-trained Transformer ​or GPT. ​Over the years, different LLMs, such as GPT-3 and GPT-4 in the GPT series, Google's Pathways ​Language Model or POM, and Meta's Large Language Model Meta-AI or LLAMA, have significantly ​enhanced generative AI to generate coherent and relevant text. ​There have been similar developments and models for other use cases. ​For example, Stable Diffusion and DALL-E are models for image generation. ​The development of a variety of generative models has led to a growing market for generative ​AI tools for diverse use cases. ​For instance, you have ChatGPT and Gemini for text generation, DALL-E2 and MidJourney ​for image generation, Synthesia for video generation, and Copilot and AlphaCode for ​code generation. 
​The rapidly emerging models and tools have generated a wide scope for generative AI applications ​across domains. ​To quote from McKinsey's report on the economic potential of generative AI, ​Generative AI has the potential to change the anatomy of work, augmenting the capabilities ​of individual workers by automating some of their individual activities. ​The report also predicts that generative AI's impact on productivity could add trillions ​of dollars in value to the global economy. ​In this video, you learned that generative AI models can generate new content based on ​the data they are trained on. ​Further, you learned that the creative skills of generative AI are built from models such ​as GANs, VAEs, transformers, and diffusion models. ​Foundation models can be adapted to create specialized models or tools tailored to specific ​use cases. ​Finally, you learned that generative AI models and tools have a wide scope for applications ​across different domains and industries. 
What are Generative AI Models?
​Over the past couple of months, ​large language models, or LLMs, ​such as ChatGPT, have taken the world by storm. ​Whether it's writing poetry or ​helping plan your upcoming vacation, ​we are seeing a step change in the performance of ​AI and its potential to drive enterprise value. ​My name's Kate Soule. ​I'm a Senior Manager of Business Strategy at IBM Research, ​and today I'm going to give a brief overview of ​this new field of AI that's emerging, ​and how it can be used in a business setting to drive value. ​Now, large language models are actually a part ​of a different class of models called foundation models. ​Now, the term foundation models was ​actually first coined by a team from Stanford. ​When they saw that the field of AI was converging to ​a new paradigm where before AI applications were being ​built by training maybe a library of ​different AI models where each AI model was ​trained on very task-specific data to perform very specific task. 
​They predicted that we were going to start moving to ​a new paradigm where we would have ​a foundational capability or a foundation model that would ​drive all of these same use cases and applications. ​So the same exact applications that we're ​envisioning before with conventional AI, ​and the same model could drive any number of additional applications. ​The point is that this model could be transferred to any number of tasks. ​That gives this model the superpower to be able to transfer ​to multiple different tasks and perform multiple different functions, ​is that it's been trained on a huge amount in ​an unsupervised manner on unstructured data. ​What that means in the language domain is basically I'll feed ​a bunch of sentences and I'm talking ​terabytes of data here to train this model. ​The start of my sentence might be, ​no use crying over spilled, ​and the end of my sentence might be milk. ​I'm trying to get my model to predict ​the last word of the sentence based off of the words that it saw before. 
​It's this generative capability of the model predicting and generating ​the next word based off of previous words that it's seen beforehand. ​That is why that foundation models are actually ​a part of the field of AI called Generative AI. ​Because we're generating something new. ​In this case, the next word in a sentence. ​And even though these models are trained to perform at its core a generation task, ​predicting the next word in the sentence, ​we actually can take these models and if you introduce ​a small amount of label data to the equation, ​you can tune them to perform traditional NLP tasks, ​things like classification or named entity recognition, ​things that you don't normally associate as being ​a generative based model or capability. ​This process is called tuning, ​where you can tune your foundation model by introducing a small amount of data, ​you update the parameters of your model, ​and now I can perform a very specific natural language task. ​If you don't have data or have only very few data points, ​you can still take these foundation models and they actually ​work very well in low label data domains. 
​In a process called prompting or Prompt Engineering, ​you can apply these models for some of those same exact tasks. ​So an example of prompting a model to perform ​a classification task might be you could give the model a sentence, ​and then ask it a question. ​Is this sentence have a positive sentiment or negative sentiment? ​The model is going to try and finish generating words in that sentence, ​and the next natural word in that sentence would be ​the answer to your classification problem, ​so it would respond either positive or negative, ​depending on where it estimated the sentiment of the sentence would be. ​These models work surprisingly well when applied to these new settings and domains. ​Now, this is a lot of where the advantages of foundation models come into play. ​So if we talk about the advantages, ​the chief advantage is the performance. 
​These models have seen so much data. ​Again, data with a capital D, ​terabytes of data, that by the time that they're applied to small tasks, ​they can drastically outperform a model that was only trained on just a few data points. ​The second advantage of these models are the productivity gains. ​So just like I said earlier, ​through prompting or tuning, ​you need far less labeled data to get to ​a task-specific model than if you had to start from scratch, ​because your model is taking advantage of all the unlabeled data that it ​saw in its pre-training when we created this generative task. ​With these advantages, there are also ​some disadvantages that are important to keep in mind. ​And the first of those is the compute costs. ​So the penalty for having this model see ​so much data is that they're very expensive to train, ​making it difficult for smaller enterprises to train a foundation model on their own. 
​They're also expensive by the time they get to a huge size, ​a couple billion parameters, ​they're also very expensive to run inference. ​You might require multiple GPUs at a time just to host these models and run inference, ​making them a more costly method than traditional approaches. ​The second disadvantage of these models is on the trustworthiness side. ​So just like data is a huge advantage for these models, ​they've seen so much unstructured data, ​it also comes at a cost, ​especially in the domain like language. ​A lot of these models are trained basically ​off of language data that's been scraped from the Internet. ​And there's so much data that these models have been trained on. ​Even if you had a whole team of human annotators, ​you wouldn't be able to go through and actually bet ​every single data point to make sure that it wasn't biased, ​didn't contain hate speech or other toxic information. 
​And that's just assuming you actually know what the data is. ​Often we don't even know for a lot of these open source models that have been posted, ​what the exact data sets are that these models have been ​trained on leading to trustworthiness issues. ​So IBM recognizes the huge potential of these technologies. ​But my partners in IBM Research are working on ​multiple different innovations to try and improve also the efficiency of these models, ​and the trustworthiness and reliability of ​these models to make them more relevant in a business setting. ​All of these examples that I've talked through so far have just been on the language side. ​But the reality is, ​there are a lot of other domains that foundation models can be applied towards. ​Famously, we've seen foundation models for vision, ​looking at models such as DALLL E2, ​which takes text data and that's then used to generate a custom image. 
​We've seen models for code with products like ​Copilot that can help complete code as it's being authored. ​And IBM's innovating across all of these domains. ​So whether it's language models that we're building into ​products like Watson Assistant and Watson Discovery, ​vision models that we're building into products like Maximo Visual Inspection, ​or Ansible code models that we're building with our partners at Red Hat under Project Wisdom. ​We're innovating across all of these domains and more. ​We're working on chemistry. ​So for example, we just published and released Moleformer, ​which is a foundation model to promote ​molecule discovery for different targeted therapeutics. ​And we're working on models for climate change. 
​Building earth science foundation models using geospatial data to improve climate research. ​I hope you found this video both informative and helpful. ​If you're interested in learning more, particularly how IBM is working to improve ​some of these disadvantages, making foundation models more trustworthy and more efficient, ​please take a look at the links below. ​Thank you. 
What is NLP (Natural Language Processing)?
​What is natural language processing? Well, you're doing it right now. You're listening ​to the words and the sentences that I'm forming and you are forming some sort of comprehension ​from it. And when we ask a computer to do that, that is NLP or natural language processing. ​My name is Martin Keene. I'm a master inventor at IBM and I've utilized NLP in a good number ​of my invention disclosures. NLP really has a really high utility value in all sorts of ​AI applications. Now, NLP starts with something called unstructured text. What is that? Well, ​that's just what you and I say. That's how we speak. So for example, some unstructured ​text is, add eggs and milk to my shopping list. Now, you and I understand exactly what ​that means, but it is unstructured, at least to a computer. So what we need to do is to ​have a structured representation of that same information that a computer can process. Now ​that might look something a bit more like this, where we have a shopping list element ​and then it has sub elements within it, like an item for eggs and an item for milk. That ​is an example of something that is structured. Now, the job of natural language processing ​is to translate between these two things. So NLP sits right in the middle here, translating ​between unstructured and structured data. And when we go from unstructured here to structured ​this way, that's called NLU, or Natural Language Understanding. And when we go this way from ​structured to unstructured, that's called Natural Language Generation, or NLG. We're ​going to focus today primarily on going from unstructured to structured in natural language ​processing. Now, let's think of some use cases where NLP might be quite handy. First ​of all, we've got machine translation. Now, when we translate from one language to another, ​we need to understand the context of that sentence. It's not just a case of taking ​each individual word from, say, English and then translating it into another language. 
​We need to understand the overall structure and context of what's being said. And my favourite ​example of this going horribly wrong is if you take the phrase, "the spirit is willing, ​but the flesh is weak", and you translate that from English to Russian, and then you translate ​that Russian translation back into English, you're going to go from the spirit is willing, ​but the flesh is weak, to something a bit more like the vodka is good, but the meat ​is rotten, which is really not the intended context of that sentence whatsoever. So NLP ​can help with situations like that. Now, the second kind of use case that I like to mention ​relates to virtual assistants, and also to things like chatbots. Now, a virtual assistant, ​that's something like Siri or Alexa on your phone, that is taking human utterances and ​deriving a command to execute based upon that. And a chatbot is something similar except ​in written language, and that's taking written language and then using it to traverse a decision ​tree in order to take an action. NLP is very helpful there. 
​Another use case is for sentiment analysis. Now, this is taking some text, perhaps an email message or a product ​review, and trying to derive the sentiment that is expressed within it. So, for example, ​is this product review a positive sentiment or a negative sentiment? Is it written as ​a serious statement or is it being sarcastic? We can use NLP to tell us. And then, finally, ​another good example is spam detection. So this is a case of looking at a given email ​message and trying to derive, is this a real email message or is it spam? And we can look ​for pointers within the content of the message. So things like overused words or poor grammar ​or an inappropriate claim of urgency can all indicate that this is actually perhaps spam. 
​So those are some of the things that NLP can provide, but how does it work? Well, the thing ​with NLP is it's not like one algorithm. It's actually more like a bag of tools, and you ​can apply these bag of tools to be able to resolve some of these use cases. Now, the ​input to NLP is some unstructured text, so either some written text or spoken text that ​has been converted to written text through a speech-to-text algorithm. Once we've got ​that, the first stage of NLP is called tokenization. This is about taking a string and breaking ​it down into chunks. So if we consider the unstructured text we've got here, add eggs ​and milk to my shopping list, that's eight words, that could be eight tokens. And from ​here on in, we are going to work one token at a time as we traverse through this. Now, ​the first stage, once we've got things down into tokens that we can perform, is called ​stemming. And this is all about deriving the word stem for a given token. So for example, ​running, runs, and ran, the word stem for all three of those is run. We're just kind ​of removing the prefix and the suffixes and normalizing the tense, and we're getting to ​the word stem. But stemming doesn't work well for every token. For example, universal and ​university, well, they don't really stem down to universe. For situations like that, ​there is another tool that we have available, and that is called lemmatization. 
​And lemmatization takes a given token and learns its meaning through a dictionary definition, ​and from there it can derive its root or its lem. So take better, for example. Better ​is derived from good, so the root or the lem of better is good. The stem of better would be bet. ​So you can see that it is significant whether we use stemming or we use lemmatization for ​a given token. Now, next thing we can do is we can do a process called part of speech tagging. ​And what this is doing is, for a given token, it's looking where that token is used within ​the context of a sentence. So take the word make, for example. If I say I'm going to make ​dinner, make is a verb. But if I ask you what make is your laptop, well, make is now a noun. So ​where that token is used in the sentence matters. Part of speech tagging can help us derive that ​context. And then finally, another stage is named entity recognition. And what this is asking is, ​for a given token, is there an entity associated with it? So, for example, a token of Arizona has ​an entity of a U.S. state, whereas a token of Ralph has an entity of a person's name. 
​And these are some of the tools that we can apply in this big bag of tools that we have for NLP ​in order to get from this unstructured human speech through to something structured that ​a computer can understand. And once we've done that, then we can apply that structured data to ​all sorts of AI applications. Now, there's obviously a lot more to it than this, and I've ​included some links in the description if you'd like to know more. But hopefully this made some ​sense, and that you were able to process some of the natural language that I've shared today. ​Thanks for watching. 
Reading: Comprehensive Guide to Generative AI
Introduction
Generative AI (GenAI) has evolved from basic text and image generation to powering complex systems such as AI agents, enterprise automation, and reasoning engines. This guide explores core concepts, tools, and frameworks for building modern GenAI applications, including RAG, multi-agent systems, prompt engineering, and cutting-edge libraries like LangGraph.
Whether you're developing chatbots, automation workflows, or knowledge systems, this guide provides a roadmap to the latest advancements. It also introduces additional terms not covered in the course videos. These terms are essential for enhancing your understanding of the course concepts.
Core GenAI Concepts & Terminologies
Foundational Concepts
Term
Definition
Examples/Use Cases
LLM
A type of AI model trained on vast amounts of text data to understand and generate human-like language.
GPT-o1, Claude, LLaMA
Prompting
A technique for designing input instructions to guide LLM outputs.
"Write a summary in 3 sentences," "Answer as a cybersecurity expert."
Prompt Templates
Reusable, structured prompts with placeholders for dynamic inputs.
"Explain {concept} like I'm 5 years old."
RAG (Retrieval-Augmented Generation)
Combines retrieval from external knowledge sources with LLM generation to enhance factual accuracy.
Answering questions with real-time data (for example, RAG Paper)
Retriever
A system component designed to fetch relevant information from a dataset or database.
Vector similarity search using FAISS, Elasticsearch
Agent
An autonomous AI system that can plan, reason, and execute tasks using tools.
AutoGPT, LangChain Agents
Multi-Agent System
A framework in which multiple AI agents collaborate to solve complex tasks.
Microsoft AutoGen, CrewAI
Chain-of-Thought
A prompting technique that encourages models to decompose problems into intermediate steps.
"Let's think step by step…"
Hallucination Mitigation
Strategies to reduce incorrect or fabricated outputs from LLMs.
RAG, fine-tuning, prompt constraints
Vector Database
A database optimized for storing and querying vector embeddings.
Pinecone, Chroma, Weaviate
Orchestration
Tools to manage and coordinate workflows involving multiple AI components.
LangChain, LlamaIndex
Fine-tuning
Adapting pre-trained models for specific tasks using domain-specific data.
LoRA (Low-Rank Adaptation), QLoRA (quantized fine-tuning)

Tools & Frameworks
Model Development & Deployment
Tool/Framework
Definition
Examples/Use Cases
Reference Link
Hugging Face
A platform hosting pre-trained models and datasets for NLP tasks.
Accessing GPT-2, BERT, Stable Diffusion
Hugging Face
LangChain
A framework for building applications with LLMs, agents, and tools.
Creating chatbots with memory and web search
LangChain
AutoGen
A library for creating multi-agent conversational systems.
Simulating debates between AI agents
AutoGen
CrewAI
A framework for assembling collaborative AI agents with role-based tasks.
Task automation with specialized agents
CrewAI
BeeAI
A lightweight framework to build production-ready multi-agent systems
Distributed problem-solving systems
BeeAI
LlamaIndex
A tool to connect LLMs to structured or unstructured data sources.
Building Q&A systems over private documents
LlamaIndex
LangGraph
A library for building stateful, multi-actor applications with LLMs.
Cyclic workflows, agent simulations
LangGraph

Retrieval & Infrastructure
Tool/Framework
Definition
Examples/Use Cases
Reference Link
FAISS
A library for efficient similarity search of dense vectors.
Retrieving top-k documents for RAG
FAISS
Pinecone
A managed cloud service for vector database operations.
Storing embeddings for real-time retrieval
Pinecone
Haystack
An end-to-end framework for building RAG pipelines.
Deploying enterprise search systems
Haystack

Advanced Prompting Techniques
Concept
Definition
Example
Few-Shot Prompting
Providing examples in the prompt to guide the model's output format.
"Translate to French: 'Hello' → 'Bonjour'; 'Goodbye' → __”
Zero-Shot Prompting
Directly asking the model to perform a task without examples.
"Classify this tweet as positive, neutral, or negative: {tweet}”
Chain-of-Thought
Encouraging step-by-step reasoning.
"First, calculate X. Then, compare it to Y. Final answer: ___”
Prompt Chaining
Breaking complex tasks into smaller prompts executed sequentially.
Prompt 1: Extract keywords → Prompt 2: Generate summary from keywords.

Key Architectures & Workflows
RAG Pipeline
Retrieval: Query vector database (for example, Pinecone) for context.
Augmentation: Combine context with user prompt.
Generation: LLM (for example, GPT-4) produces final output.
Multi-Agent System
Agents: Specialized roles (for example, researcher, writer, critic).
Orchestration: LangGraph for cyclic workflows, AutoGen for conversations, and so on.
Tools: Web search, code execution, API integrations, and so on.
References
Retrieval-Augmented Generation (RAG) Paper
Chain-of-Thought Prompting
LangGraph Documentation
CrewAI Documentation
Prompt Engineering Guide



Working with Prompt Engineering and Prompt Templates
Introduction to In Context Learning
​Welcome to Introduction to In-context Learning. ​After watching this video, you'll be able to describe in-context learning. ​You will also be able to explain the fundamentals of prompt engineering. ​In-context learning is a specific method of prompt engineering where demonstrations ​of the task are provided to the model as a part of the prompt in natural language. ​However, in-context learning doesn’t require additional training. ​A new task is learned from a small set of examples presented within the context or ​prompt at inference time. ​Let's understand some advantages and disadvantages of in-context learning. 
​In-context learning doesn't require the model to be fine tuned on specific ​datasets. ​This can drastically reduce the resources and time needed to adapt LLMs for ​specific tasks while improving their performance. ​While in-context learning is efficient, ​it's constrained by what can realistically be provided in the context. ​Complex tasks could require gradient steps or ​more traditional machine learning training approaches, ​which involve adjusting the model's weights based on error gradients. ​Next, let's learn about prompt engineering. ​Let's begin by understanding what prompts are and ​their role in interacting with AI systems. ​Essentially, prompts are instructions or inputs given to an LLM designed to ​guide it toward performing a specific task or generating a desired output. 
​There are two main components to a prompt. ​Instructions are clear, direct commands that tell the AI what to do. ​They need to be specific to ensure the LLM understands the task. ​Context includes the necessary information or ​background that helps the LLM make sense of the instruction. ​It can be data, parameters, ​or any relevant details that shape the AI's response. ​By combining these elements effectively, ​you can tailor LLMs like those developed by IBM, OpenAI, Google, or Meta to perform ​tasks ranging from answering queries and analyzing data to generating content. ​Prompt engineering is a specialized process where you design and ​refine the questions, commands, ​or statements you use to interact with the AI systems, particularly LLMs. 
​The goal is not just about asking a question, ​it's about how to ask it in its best way possible. ​This involves carefully crafting clear, contextually rich prompts tailored to get ​the most relevant and accurate responses from the AI. ​This process is fundamental in fields ranging from customer service automation ​to advanced research and computational linguistics. ​Now that you are familiar with prompt engineering, ​let's delve into why its crucial for enhancing AI capabilities. ​Prompt engineering boosts effectiveness and ​accuracy by directly influencing how effectively and accurately LLMs function. ​It ensures relevance by enabling LLMs to generate precise and ​perfectly suited responses to the context. ​It facilitates meeting user expectations through clearer prompts and ​reduced misunderstandings. 
​It eliminates the need for continual fine-tuning, ​allowing the model to adapt and learn within its context. ​Here is an example of a prompt given to GPT 3.5. ​The wind is ​This simple prompt leads to a poetic response. ​Blowing gently through the trees, whispering secrets and ​stories to anyone who cares to listen. ​You can see how an open ended prompt can guide the LLM to create imaginative and ​detailed responses, highlighting its ability to generate creative and ​engaging content. ​Let's break down the components that make up a well structured prompt. ​Instructions tell the LLM what needs to be done. 
​For example, classify the following customer review into neutral, negative, or ​positive sentiment. ​This is straightforward and directs the LLMs action. ​Context helps the LLM understand the scenario or ​the background in which it operates. ​Here it's indicated that this review is part of feedback for ​a recently launched product. ​This can help the LLM weigh the sentiment analysis in light of the products novelty. ​Input data is the actual data the LLM will process. ​In the prompt, it's the customer review. 
​The product arrived late but the quality exceeded my expectations. ​The LLM uses this data to perform the task specified by the instructions. ​The output indicator is the part of the prompt where the LLM's response is ​expected. ​It's a clear marker that tells the AI where to deliver its analysis. ​In this example, sentiment indicates waiting for ​the LLM to append its classification. ​Let's recap. ​In this video, you learned that in-context learning is a method of prompt engineering ​where task demonstrations are provided to the model as a part of the prompt. 
​Prompts are inputs given to an LLM to guide it towards performing ​a specific task. ​They consist of instructions and context. ​Prompt engineering is a process where you design and ​refine the prompts to get relevant and accurate responses from AI. ​Prompt engineering has several advantages. ​It boosts the effectiveness and accuracy of LLMs. ​It ensures relevant responses. ​It facilitates meeting user expectations. 
​It eliminates the need for continual fine tuning. ​A prompt consists of four key elements, instructions, context, input data, ​and output indicator. 
Introduction to LangChain
Warning: 6 XP • Prototyping and Strategic Evaluation of Generative AI
6 XP • Prototyping and Strategic Evaluation of Generative AI
Dive deeper on this topic
​Welcome to this introduction to LangChain. ​After watching this video, you`ll be able describe LangChain`s purpose, ​discuss its benefits, devise practical uses for LangChain, ​explain how LangChain works with other data types. ​The LangChain open-source Python framework streamlines the development of large ​language model (LLM) applications. ​LangChain provides developers with components and ​interfaces to assist in integrating LLMs into their AI applications. ​The framework is used to pinpoint relevant information in text, ​such as a research paper or legal document. ​It also provides methods for responding to complex prompts by retrieving data and ​generating a coherent summary. ​It chains together the retrieval, extraction, processing, ​and generation operations from the large amounts of text and multiple sources, ​hence the word chain as part of its name. 
​AI developers prefer this framework because of several key benefits, ​including its modularity, extensibility, and decomposition capabilities. ​It also easily integrates with vector databases. ​Let's discuss each of these. LangChain's design allows application developers ​to piece together different components like building blocks. ​This modularity also encourages component reuse, reducing development time and ​effort. ​LangChain's extensible design allows developers to readily add new features, ​adapt to existing components, integrate with external systems, and ​make only minimal changes to their codebases. ​LangChain mimics the human problem-solving process by breaking down complex queries ​or tasks into smaller, manageable steps. 
​This decomposition capability enables it to make accurate inferences from context, ​resulting in relevant, precise responses. ​LangChain integrates with vector databases for efficient semantic searches and ​information retrieval. ​When used in conjunction with vector databases, it provides applications quick ​access to relevant information within extensive data sets. ​AI applications can leverage the LangChain framework for ​a number of practical uses such as content summarization, data extraction, ​sophisticated question and answer systems, and ​automated content generation. Let's explore a specific example of each. ​With its ability to summarize articles, reports, and documents, users can stay ​better informed by deciphering the meaning of complex legal documents. ​It can extract key statistics from reports, ​simplifying the process of turning text into actionable insights. 
​Question and answer systems with LangChain can transform customer support and ​knowledge-based services. ​These systems can provide contextually relevant answers to a chain of clarifying ​responses based on the entire conversation. ​LangChain can assist with the generation of written materials. ​The framework opens possibilities for automating routine ​writing tasks such as drafting emails, brainstorming, or technical documentation. ​While primarily designed for text based applications, ​LangChain can work with other data types such as images, audio, ​and video by leveraging external libraries and models like speech to text. ​Its integration with vector databases enables the use of embeddings generated ​from these data types to capture semantic meaning and perform similarity searches, ​making it a valuable tool for various AI tasks. ​In this video, you learned that LangChain is a Python framework for ​pinpointing relevant information and text and providing methods for ​responding to complex prompts. 
​Benefits include modularity, extensibility, decomposition capabilities, ​and easy integration with vector databases. ​Several practical applications include deciphering complex legal documents, ​extracting key statistics from reports, customer support, and ​automating routine writing tasks. ​LangChain can be used with other data types by using ​external libraries and models. 
Advanced Methods of Prompt Engineering
​Welcome to advanced methods of prompt engineering. ​After watching this video, ​you'll be able to apply ​advanced methods of prompt engineering ​to enhance prompt design. ​You will also be able to ​discuss the effective implementation of ​the tools and applications of ​prompt engineering to real world scenarios. ​In this example, you will learn about a zero-shot prompt. ​This type of prompt instructs an LLM to perform ​a task without any prior specific training or examples. ​Here, the LLM is asked to ​classify a statement as true or false. ​The Eiffel Tower is located in Berlin. 
​Then the model gives the response. ​This task requires the LLM to understand the context ​and information without any previous tuning ​for the specific query. ​A one-shot prompt gives the LLM ​a single example to help it perform a similar task. ​For example, how is the weather today? ​The LLM shows how to ​translate a sentence from English to French. ​This serves as a template. ​Then it's given a new sentence, ​where is the nearest supermarket, ​and is expected to translate it ​into French using the learned format. 
​The AI uses the initial example ​to correctly perform the new translation. ​Another method is few-shot prompting where the AI ​learns from a small set of ​examples before tackling a similar task. ​This helps the AI generalize ​from a few instances to new data. ​For example, the LLM is shown three statements, ​each labeled with an emotion. ​These examples teach the LLM to ​classify emotions based on context. ​Then it classifies a new statement. ​That movie was so scary. 
​I had to cover my eyes. ​The LLM will output the emotion. ​Chain-of-thought or COT prompting is ​a technique used to guide ​LLM through complex reasoning step-by-step. ​This method is highly effective for problems requiring ​multiple intermediate steps or ​reasoning that mimics human thought processes. ​The example shows how ​CoT prompting is applied to an arithmetic problem. ​The prompt asks the model to consider the problem of ​a store that initially had 22 apples, ​sold 15, and then ​received a new delivery of eight apples. ​The task is to determine how many apples there are now. 
​You can view the model output for the CoT prompt query ​by breaking down the calculation ​into clear sequential steps. ​The model arrives at ​the correct answer and provides ​a transparent explanation. ​Self-consistency is a technique for ​enhancing the reliability and accuracy of outputs. ​It involves generating multiple independent answers to ​the same question and then evaluating ​these to determine the most consistent result. ​In this example, you see ​a problem involving age calculation. ​The query is, when I was six, ​my sister was half my age. ​Now I am 70. What age is my sister? 
​The model is prompted to produce ​three independent calculations and ​explanations to ensure accuracy. ​You can view the model outputs with ​three different ways of calculation ​and determine a consistent answer. ​This approach demonstrates how ​self-consistency can verify the reliability of ​the responses from LLMs by ​cross-verifying multiple paths to the same answer. ​Next, let's explore the tools and ​applications used in prompt engineering. ​Certain tools can facilitate interactions with LLMs, ​such as OpenAI's Playground, LangChain, ​Hugging Face's Model Hub, ​and IBM's AI Classroom. ​They allow you to develop, ​experiment with, evaluate, and deploy prompt. ​They enable real-time tweaking and testing of ​prompt to see immediate effect on outputs. 
​Moreover, they provide access to ​various pre-trained models suitable ​for different tasks and languages. ​They also facilitate ​the sharing and collaborative editing ​of prompts among teams or communities. ​Finally, they offer tools to track changes, ​analyze results, and optimize ​prompt based on performance metrics. ​Let's learn more about LangChain, ​a tool for prompt engineering. ​LangChain uses prompt templates, ​predefined recipes for generating ​effective prompt for LLMs. ​These templates include ​instructions for the language model, ​a few-shot examples to help the model ​understand contexts and expected responses, ​and a specific question directed at the language model. ​Here is a code snippet to ​apply a prompt template from LangChain. 
​First, import the prompt template ​from LangChain core prompts. ​Then define a joke prompt template, ​tell me a joke about. ​This template has placeholders ​for an adjective and the content. ​To use the template, call prompt template format with ​specific values funny for ​the adjective and chickens for the content. ​This generates the prompt, ​tell me a funny joke about chickens. ​This approach simplifies prompt creation, ​making prompt consistent and ​adaptable to different contexts. ​In prompt applications, an agent is a crucial concept. 
​Powered by LLMs and integrated tools like LangChain, ​agents perform complex tasks ​across various domains using different prompts. ​Transformative applications ​include Q&A agents with sources, ​content agents for creation and summarization, ​analytic agents for ​data analysis and business intelligence, ​and multilingual agents for ​seamless context aware translation and communication. ​Let's recap. In this video, ​you learned that advanced methods for ​prompt engineering include zero-shot prompt, ​few-shot prompt, chain-of-thought prompting, ​and self-consistency. ​Tools can facilitate interactions with LLMs. ​LangChain uses prompt templates ​to generate effective prompts. ​In prompt applications, an agent can perform ​complex tasks across domains using different prompts. 
LangChain LCEL Chaining Method
​Hello, and welcome to this video on the LangChain LCEL Chaining Method. ​After watching this video, you'll be able to ​Describe how to build flexible, composable chains using LangChain's modern approach to prompt engineering. ​Structure prompts effectively using templates. ​Connect components using the pipe operator to streamline workflows. ​And develop reusable patterns for a variety of AI applications. ​LangChain Expression Language (or LCEL) is a pattern for building LangChain applications ​that utilizes the pipe (|) operator to connect components. ​This approach ensures a clean, readable flow of data from input to output. 
​LangChain has evolved significantly, and this video will focus on the newer, recommended ​LCEL pattern rather than the traditional LLM chain approach. ​This modern method provides better composability, clearer visualization of data flow, and greater ​flexibility when constructing complex chains. ​To create a typical LCEL pattern, you need to ​Define a template with variables and curly braces ​Create a prompt template instance. Build a chain using the pipe operator to connect components. Invoke the chain with input values. ​Let's see this in action with a concrete example. ​In LangChain, runnables serve as an interface and building blocks that connect different ​components like LLMs, retrievers, and tools into a pipeline. 
​There are two main runnable composition primitives. ​Runnable sequence chains components sequentially, passing the output from one component as input to the next. ​RunnableParallel runs multiple components concurrently while using the same input for each. ​However, LCEL provides elegant syntax shortcuts. ​For example, instead of using runnable sequence, the same sequential chain can be created by ​simply connecting runnable 1 and runnable 2 with a pipe, making the structure more readable and intuitive. ​LCEL also handles type coercion automatically. ​This means it converts regular code into runnable components. 
​When you use a dictionary, it becomes a runnable parallel, which runs multiple tasks simultaneously. ​When you use a function, it becomes a RunnableLambda, which transforms inputs. ​This happens behind the scenes, so you don't have to handle the conversion manually. ​For example, in this code, the pipe operator combines the prompt templates with the LLM. ​The dictionary structure creates a RunnableParallel which processes all three tasks simultaneously. ​Each task receives the same input, text, but processes it differently. ​When you run this, it automatically becomes a RunnableParallel. 
​The result will contain three keys, summary, translation, and sentiment, each with the output from the respective LLM call. ​Let's see LCEL in action by creating a simple chain. ​This code demonstrates how components can be connected using the pipe operator. ​The RunnableLambda in this chain wraps the format_prompt function, transforming it into ​a runnable component that LangChain can work with. ​When the chain runs, RunnableLambda takes the input dictionary, containing adjective ​and content keys, passes this dictionary to the format_prompt function. ​The function formats the prompt template with these variables. ​The formatted prompt is then passed to the next component, the LLM. 
​The pipe operator creates a sequence by connecting runnable components together. ​In this joke chain, first, the RunnableLambda formats the prompt with variables. ​The pipe operator passes the formatted prompt to the LLM. ​Another pipe passes the LLM's response to the StrOutputParser. ​We've covered the essentials of LCEL, from its benefits and composition primitives to ​building practical chains using the pipe operator. ​Keep in mind that LCEL is best suited for simpler orchestration tasks. ​For more complex workflows, consider using LangGraph while still leveraging LCEL within individual nodes. 
​As you develop your own applications, take advantage of LCEL's strengths, including ​parallel execution, async support, simplified streaming, and automatic tracing. ​These capabilities enhance both the power and maintainability of your applications. ​In this video, you learned that ​LCEL pattern structures workflows use the pipe operator for clear data flow. ​Prompts are defined using templates with variables and curly braces. ​Components can be linked using RunnableSequence for sequential execution. ​RunnableParallel allows multiple components to run concurrently with the same input. ​LCEL provides a more concise syntax by replacing RunnableSequence with the pipe operator. 
​Type coercion in LCEL automatically converts functions and dictionaries into compatible components. 
Reading: What is Prompt Engineering, and Why Do We Care?
Introduction
In this lab, we'll introduce the concept of prompt engineering and how it can help you leverage what AI offers. Before jumping in, we should define Prompt Engineering, why it matters, and how we got to this point in the AI landscape.
If you've ever used a chatbot or virtual assistant online, you may have mixed feelings about the experience. Most chatbots are designed to respond to a predefined set of queries programmatically. While AI allows some flexibility in how we phrase our messages, these chatbots are essentially programmed with specific responses.
A well-designed chatbot can still provide a pleasant user experience, but often lacks a 'wow' or 'magic' factor. A user interacting with a good chatbot is unlikely to be amazed by its AI capabilities. On the other hand, poor chatbots—of which there are many—can be frustrating, often leading users to angrily type 'AGENT!!!' after just a few exchanges.
A first taste of AI
It's no surprise then that the world took serious notice when OpenAI's ChatGPT, Google Bard, watsonx, and similar AI chatbots became available. ChatGPT, for example, gained a million users within just five days of its launch in November 2022. For comparison, some of the fastest-growing apps in the world took several weeks to reach that milestone.
For the first time, conversational generative AI chatbots truly amazed us. The conversations felt natural, and the answers were both plausible and valuable.
Behind the scenes, complex mathematics and vast amounts of data are used to train large language models (LLMs), which power conversational AI. Fortunately, you don't need to worry about the intricate implementation details to take full advantage of their capabilities.
The experience is remarkably similar to engaging with a brilliant individual possessing vast knowledge equivalent to terabytes of data.
People have started using such chatbots to boost productivity, communicate more clearly, quickly summarize large amounts of data, and assist with decision-making.
LLMs are powerful technologies that have the potential to transform industries and the world at large.
So, we have this incredible tool—how can we make the most of it?
It all starts with user input, our prompt. A simple text box is all we have to control this powerful tool. The quality of our prompt significantly impacts the results (the output). As the saying goes, 'garbage in, garbage out.' If we provide a vague or poorly structured prompt, the AI won't have much to work with, limiting its ability to deliver valuable responses and showcase its full potential.
What is prompt engineering?
For example, let's ask one of the aforementioned LLM-based AIs, 'What is Prompt Engineering?'
This is the result I got:
Prompt engineering refers to the process of designing and refining prompts or instructions given to a language model, such as GPT-3.5, to generate desired outputs. It involves carefully crafting the input text provided to the model to elicit the desired response or behavior.
Prompt engineering can be used to fine-tune the output of language models by specifying explicit instructions, adding context, or using specific formatting techniques to guide the model's generation. By tweaking the prompts, developers and users can influence the output to be more accurate, coherent, or aligned with a specific goal.
Effective prompt engineering requires understanding the underlying language model and its capabilities. It involves experimenting with different prompts, iterating on them, and analyzing the model's responses to achieve the desired results. Prompt engineering is particularly important Prompt engineering is crucial when working with large language models like GPT-3.5, as their responses can occasionally be unpredictable or need extra context to produce the desired results.
Overall, prompt engineering is a crucial aspect of working with language models to ensure they produce accurate and meaningful responses that align with the user's intentions or requirements.
Not bad, eh? This AI technology might be quite useful. In this course, you'll learn everything you need to know to optimize the results you get from conversational AI, regardless of which specific LLM you choose to use.
Zero-shot, one-shot, and few-shot prompting
In the realm of large language models (LLMs) like GPT-3.5, you may come across terms such as zero-shot, one-shot, and few-shot prompting. These terms describe different ways of instructing or prompting the model.
In a zero-shot scenario, the model is given a task without any prior examples. It must determine what to do based solely on the prompt and its training.
In the next couple of labs, we'll refer to naive or standard prompting a few times. This refers to the type of prompt used by someone unfamiliar with LLM-based AI. They'd ask their question without providing any examples for the model.
For example, when we asked, 'What is Prompt Engineering?', we used a zero-shot prompt.
In contrast, a one-shot prompt provides the model with a single example, while a few-shot prompt includes multiple examples to guide its output. These techniques help shape the model's responses, especially when it hasn't been explicitly trained for a particular task. Users can steer the model toward a specific output or format by offering examples.
Chain-of-thought (CoT), a more advanced prompting technique explored later in the course, is an example of one-shot prompting (or few-shot prompting, depending on how we phrase our prompt).
1. Did the fake-LLM cell run? Did the asserts pass, and what did the printed prompt look like? If it failed, paste the error.
It passed, with no error

2. The core idea. In your own words, why does RunTemplate accept llm: LLMPort instead of just creating a ChatOpenAI inside itself?
Because we designed the port and defined a fakellm using ducktyping so that it can be swapped out and easier 

3. Structural typing. FakeLLM never says it implements LLMPort. Why does that still work, and what would happen if you had named its method generate_text?
It will not work, because it will identify as a LLMPort
If we renamed, the shapes will not match 

4. The pipe. In self.template | RunnableLambda(...), what goes in on the left, what comes out, and why is .to_string() needed?
What i know is that, it is a left to right execution. So it will take the template but honestly I dont know how exactly it works 



