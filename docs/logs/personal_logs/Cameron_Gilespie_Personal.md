## Dates of Sprint: (10/26/2025 – 11/1/2025)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src= "https://github.com/COSC-499-W2025/capstone-project-team-2/blob/Cameron-Personal-Logs/docs/logs/peer_eval_screenshots/PL-CameronG-11-8-25.png" />


### Features Worked on this Milestone (Provide sufficient detail)
  * #1: Create Database


## Associated Tasks from Project Board:

| Description        | Status   |
| ------------------ | -------- |
| [Create Database]  | [Complete] |



---
## Next week goals
The goals for Week 6:
- Expand the database some more
- dig deeper into docker
- add helper functions so we can load and pull documents from db easier
---

### Extra Details:

<details>
So I set out this week to set up the database and edit the functions i set up last week to properly use mysql. Of which i completed and now can create the database and all appropriate tables. I really wanted to set up helper functions so that way we can just call those methods and it pulls data types, uploads the files,etc this week but i struggled with two things. the Delay in my inital PR this week being merged as well as struggling with the mysql connection. I struggled particularily hard with getting the connection up and going between verision mismatches, ports and then docker set up changing a bit due to the win32 security import when it is built. after solving these issues I managed to get the task done. but i will be working hard over the reading break to ensure i get everything i want done and then some to make up for the unfortunate trouble shooting that i needed to do with SQL and Docker

</details>

## Dates of Sprint: (10/26/2025 – 11/1/2025)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src= "https://github.com/COSC-499-W2025/capstone-project-team-2/blob/Cameron-Personal-Logs/docs/logs/peer_eval_screenshots/PL_CameronG_11_1_25.png" />


### Features Worked on this Milestone (Provide sufficient detail)
  * #1: Add the foundation for Docker integration for the database and app containerization


## Associated Tasks from Project Board:

| Description        | Status   |
| ------------------ | -------- |
| [Add the foundation for Docker integration for the database and app containerization]  | [Complete] |



---
## Next week goals
The goals for Week 6:
- Expand the docker integration for database launch/ creation
- start putting together our application
---

### Extra Details:

<details>
The main goal of this week was to set the foundation for docker continering our application as well as laying the foundation for establishing our database. I didnt do much this week the the grandscheme of things due to still being in exam season. Now that all exams are resolved I plan on planning out our next stages for app containerization as possibly setting up the database that we require. I also hope we start planning out the entry point as well as assembling all our code to create the demo

</details>

## Dates of Sprint: (10/19/2025 – 10/25/2025)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src= "https://github.com/COSC-499-W2025/capstone-project-team-2/blob/Cameron-Personal-Logs/docs/logs/peer_eval_screenshots/PL_CameronG_10_25_25.png" />


### Features Worked on this Milestone (Provide sufficient detail)
  * #1: add file ownership input
  * #2 refactor the Data extractor to output a dictionary 
  * #2: research Docker integration


## Associated Tasks from Project Board:

| Description        | Status   |
| ------------------ | -------- |
| [add file ownership input]  | [Complete] |
| [refactor the Data extractor to output a dictionary]  | [Complete] |
| [research Docker integration]  | [Complete] |


---
## Next week goals
The goals for Week 6:
- Discuss docker integration
- possibly add Json file output for data
- discuss exploring new tasks
---

### Extra Details:

<details>
So the primary goal of mine was to hop onto a new coding task this week however, that did not occur this week unfortunately due to a miscommunication between myself and a team member. So i continued finalizing the metadata extractor so that way it continues evolving with our current archetecture since it originally just outputted a string of values. now it should be outputting a full dictonary which we can utilize and transpose into a savable json file. I really hope to hop onto a different coding task to continue trying to learn python as a whole. I would also like to reflect on the fact that I did get alittle sick this week on wednesday and while already aiming to make up for just adapting the same bit of code week after week I am hoping to reach further and do more in the coming weeks.

</details>


## Dates of Sprint: (10/13/2025 – 10/19/2025)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src="https://github.com/COSC-499-W2025/capstone-project-team-2/blob/Cameron-Personal-Logs/docs/logs/peer_eval_screenshots/PL-CameronG-10-19-25.png" />


### Features Worked on this Milestone (Provide sufficient detail)
  * #1: Refinement of the File Directory Scanner
  * #2 Integrating MetaData Extraction into the Scanner
  * #2: code review


## Associated Tasks from Project Board:

| Description        | Status   |
| ------------------ | -------- |
| [Refinement of the File Directory Scanner]  | [Complete] |
| [Integrating MetaData Extraction into the Scanner]  | [Complete] |
| [Code Review]  | [Complete] |


---
## Next week goals
The goals for Week 6:
- Discuss issues on Kanban board for next steps
- Identification of group/individual projects

---

### Extra Details:

<details>
The primary goal for me this week was the finalize the overall system of my directory scanner and then provide integration regarding the extraction of types of meta data contained with in the files. As of completion it can extract the author, creation/modification date, size, as well as the types of files it pulls. I ultimately want to give a big thank you to Samantha for her insight and assistance with my code review this week since unfortunately I made some rather large errors with it in the previous sprint that I have now fully corrected. This has been an huge learning experience for myself as a whole with python programming. My hope for next week is that I can tackle the identification of group/individual projects in the upcoming week and apply the learning I have gained this week to the project going forward.

</details>




## Dates of Sprint: (10/6/2025 – 10/11/2025)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src="https://github.com/COSC-499-W2025/capstone-project-team-2/blob/Cameron-Personal-Logs/docs/logs/peer_eval_screenshots/CGill_Peer_Eval_10-11-25.png" />


### Features Worked on this Milestone (Provide sufficient detail)
  * #1: Creation file Heirarchy scanner
  * #2: code review


## Associated Tasks from Project Board:

| Description        | Status   |
| ------------------ | -------- |
| [Creation file Heirarchy scanner]  | [Complete] |
| [Code Review]  | [Complete] |


---
## Next week goals
The goals for Week 6:
- Discuss issues on Kanban board for next steps
- Evolve the Heirarchy Scanner to extract basic data from files

---

### Extra Details:

<details>
My primary goal was to create essentially the skeleton for our file data extraction which first required a program able to pull in the files from a specific directory and then detect the file structure. The proof of this is in the output of all the file names in the correct directory structure. In the coming weeks I plan to further evolve this to collect data such as Modification Dates, Creation dates as well as anything else we might include in our project. I also this week provided some overview to Immanuel to discuss his coding segment as well as to ensure my own understanding of python was correct given this was my first time coding in python

</details>

## Dates of Sprint: (09/28/2025 – 10/05/2025)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src="https://github.com/COSC-499-W2025/capstone-project-team-2/blob/Cameron-Personal-Logs/docs/logs/peer_eval_screenshots/03-10-2025_peerEval-Cameron-Gillespie.png" />


### Features Worked on this Milestone (Provide sufficient detail)
  * #1: Creation of DFD level 1 & 0


## Associated Tasks from Project Board:

| Task ID | Description        | Feature   | Assigned To | Status   |
| ------- | ------------------ | --------- | ----------- | -------- |
| [N/A]   | [Creation of DFD level 1 & 0] | [N/A] | [ALL]  | [Complete] |


---
## Next week goals
The goals for Week 6:
- Update repo README with link to system final system architecture diagram with explanation
- Update repo README with link to DFD Level 1 with explanation
- Update repo README with link to revised WBS

---

### Extra Details:

<details>
The primary focus this week for me was the completetion of the DFD level 1 and level 0, I provided input on the final product once completed and also created a channel in our server so we can keep track of who is doing what.

</details>

## Dates of Sprint: (09/20/2025 – 09/28/2025)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src="https://github.com/COSC-499-W2025/capstone-project-team-2/blob/Cameron-Personal-Logs/docs/logs/peer_eval_screenshots/Cameron-Peer-Review%209-27-25.png" />


### Features Worked on this Milestone (Provide sufficient detail)
  * #1: Project Proposal creation/refinement 


## Associated Tasks from Project Board:

| Task ID | Description        | Feature   | Assigned To | Status   |
| ------- | ------------------ | --------- | ----------- | -------- |
| [N/A]   | [Refinement of Project Proposal] | [N/A] | [ALL]  | [Complete] |


---
## Next week goals
The goals for Week 5:
- Work on creating Data flow diagram (DFD1) for our project

---

### Extra Details:

<details>
The primary focus this week for me was the completetion of the project proposal and I was tasked with the documentation of the team log this week.

</details>

## Dates of Sprint: (09/15/2025 – 09/21/2025)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src="https://github.com/user-attachments/assets/1cd5aa35-ccdd-41b8-a9e8-a50ae9f1a9c3" />


### Features Worked on this Milestone (Provide sufficient detail)
  * #1: Discussed with team and got the project requirements created and refined


## Associated Tasks from Project Board:

| Task ID | Description        | Feature   | Assigned To | Status   |
| ------- | ------------------ | --------- | ----------- | -------- |
| [N/A]   | [Completion of Project requirments] | [N/A] | [ALL]  | [Complete] |
| [N/A]   | [Establishing REPO]| [N/A]     | [ALL]       | [Complete]|



### Extra Details:

N/A
<details>
