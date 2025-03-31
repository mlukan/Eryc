# Eryc
As [Erythrocyte](https://en.wikipedia.org/wiki/Erythrocyte). This chatbot was built during the Rasa-Agent-Building-Challenge as a voluntary initiative to support the [NTS SR](https://www.ntssr.sk) (National Transfusion Service of the Slovak Republic) website with chatbot functionality. The NTS runs 12 blood donation centres around the country,supporting more than 100 thousand regular blood donors and another 200 thousand sporadic donors. Eryc is designed to answer any questions related to blood donation and help users to manage their blood donations. 
## Chatbot capabilities:
1. Semantic search based on FAISS with text-embedding-3-large model embeddings. A response augmenting agent rephrases and enhances the responses.
2. User registration and OTP authentication for any user-specific tasks. Users are authenticated using e-mail and temporary access code before.
3. Donation appointment booking, cancellation and rebooking.
4. Handling donor elligibility for donation based on  gender, previous donation date and health condition.
5. Filling out pre-donation health survey.
6. Collecting user feedback. Questions, bot answers and feedbacks are collected in a database for continuous improvement.
7. Bilingual communication (English, Slovak)
## Architecture:
1. Rasa CALM for dialogue handling
2. Agentic RAG with FAISS vector store and gpt-4o model as response rephraser/augmentor
3. Rasa action server for backend actions
4. SQlite DB with SQLAlchemy ORM to store users, locations, bookings, surveys and feedbacks. 
#### Rasa CALM Flows
- flow\_authenticate\_user
- flow\_book_donation\_slot
- flow\_cancel\_booking
- flow\_donation\_questionnaire
- flow\_feedback
- flow\_register\_user
- flow\_search\_faiss
#### Custom features
- Custom single step LLm command generator, which can handle omitted feedback and unwanted digressions 
- 18 custom actions
### Author
Martin Lukáň, PhD., mlukan#gmail.com, [www.linkedin.com/in/mlukan](www.linkedin.com/in/mlukan), [https://github.com/mlukan/Eryc](https://github.com/mlukan/Eryc)

Background graphic kindly provided by [Vecteezy](https://www.vecteezy.com)
