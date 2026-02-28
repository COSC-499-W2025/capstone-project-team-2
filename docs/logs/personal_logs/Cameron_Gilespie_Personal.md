## Dates of Sprint: (02/08/2026 – 02/29/2026)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src= "https://github.com/COSC-499-W2025/capstone-project-team-2/blob/Cameron-Personal-Logs/docs/logs/peer_eval_screenshots/PL_Cameron_02_28_26.png" />


### Features Worked on this sprint (Provide sufficient detail)
  * #1: Multi-project uploads
  * #2: Demo Video



### Tasks for Prior Week
  * Timstamp primary key





## Associated Tasks from Project Board:

| Description        | Status   |
| ------------------ | -------- |
| [Database Versioning]  | [Complete] |
| [Timstamp primary key]  | [Complete] |


## Published PRs (Excluding PL/TLs)
 * [Multi-project uploads](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/448)
 * [Timstamp primary key](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/408)



## Reviewed PRs
  * [fix ranking and clarity about the metrics#445](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/445)
  * [433 implement thumbnail management as api endpoints#434](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/434)
  * [401 default save config issue#402](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/402)
  * [Fix project re-analysis, versioning, and duplicate detection#400](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/400)



---
## Next week goals
- N/A until team meeting

### Extra Details:

<details>
For the prior two weeks I have put a larger emphasis on completing work for other classes and my midterms. I didnt contribute any new PR's during reading break, the PR's that I did contribute are from before/ after the break. first one being Timestamp primary key, which is an iteration on a prior PR which altered the primary key of our databse to project name. the second pr done with week multiproject uploads allows for users to upload multiple projects at the same time and our program will analyze them all at once returning several analyzed files at the samme time. this is done through parrallelizing our input code and assisgning worker to proform analysis on each project independently. I have also been working on the team log for this week as the video demo in tandem with samantha
</details>

## Dates of Sprint: (1/27/2026 – 2/8/2026)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src= "https://github.com/COSC-499-W2025/capstone-project-team-2/blob/Cameron-Personal-Logs/docs/logs/peer_eval_screenshots/PL_Cameron_01-08-26.png" />


### Features Worked on this sprint (Provide sufficient detail)
  * #1: Database Refactoring
  * #2: Additional Database Functionality


### Tasks for Prior Week
  * Database Versioning



## Associated Tasks from Project Board:

| Description        | Status   |
| ------------------ | -------- |
| [Database Versioning]  | [Complete] |
| [Database Refactoring]  | [Complete] |
| [New Databse Helper Functions]  | [Complete] |

## Published PRs (Excluding PL/TLs)
 * [Database-analysis versioning#352](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/352)
 * [Database updates#388](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/388)


## Reviewed PRs
  * [Add deduplication across uploads with API output and tests#358](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/358)
  * [295 convert portfolio generation into fastapi format#374](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/374)
  * [Project file traverser for sorting files into analyzers#356](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/356)
  * [342 review of test coverage#353](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/353)
  * [Print statements converted to error raising for API add on in analysis_service.py#348](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/348)
  * [296 convert resume generation into fastapi format#375](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/375)




---
## Next week goals
- N/A until team meeting

### Extra Details:

<details>
So the last two weeks I have set out to augment our current database into something more usable for the project going forward. Up until this point it was hastily built after a period of suddenly changing requirements which landed us with a usable database that didnt entirely align with what we want now. Originally Last week I created a storage system to keep track of versions of project generations and allow the user to pull prior versions should they desire, The issue with this is that the original DB utilized an incrimenting ID that the team struggled to track and pull this week I changed it over to utilizing the project names assuming they dont change. Furthermore, this week I added serveral helper functions that should help us keep track of the database health but also allow us to possibly manage how many saved versions we keep per project which is functionality I feel should have been included in the prior weeks work. However, going forward from here I am conifdent enough to say I doubt there will need to be any more refactoring to the DB especially since I believe I solved the double saving problem as well as alteration of Primary keys and the database schema as a whole going forward.
</details>

## Dates of Sprint: (1/18/2026 – 1/26/2026)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src= "https://github.com/COSC-499-W2025/capstone-project-team-2/blob/Cameron-Personal-Logs/docs/logs/peer_eval_screenshots/PL_Cameron_1-24-26.png" />


### Features Worked on this Milestone (Provide sufficient detail)
  * #1: C# Analysis




## Associated Tasks from Project Board:

| Description        | Status   |
| ------------------ | -------- |
| [C# analyzer]  | [Complete] |




---
## Next week goals
- complete C# analyzer
- work out aggregation issues

### Extra Details:

<details>
this week i set out to complete the final piece of c code analyzer logic, which was completed with relative ease given it uses similar logic to the CPP analyzer. Throught the process it was really intresting re-assembling the the analyzer restructuring it to handle C# and finding that there is some logic that actually doesnt need to be changed so i refactored my CPP analyzer to have those duplicate methods in a seperate file so i can share them between the two analyzers AND theoretically after some more digging I might be able to shift my C# analyzer into other languages given they are a similar structure now having built this sort of analyzer twice. I also did some research into our aggregation issues and have found a few small solutions that should solve our troubles. this wasent an explicit task this week but i wanted to do it regardless.


</details>

## Dates of Sprint: (1/11/2026 – 1/18/2026)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src= "https://github.com/COSC-499-W2025/capstone-project-team-2/blob/Cameron-Personal-Logs/docs/logs/peer_eval_screenshots/PL_Cameron_01-17-26.png" />


### Features Worked on this Milestone (Provide sufficient detail)
  * #1: CPP Analysis
  * #1: Documentation Refactor



## Associated Tasks from Project Board:

| Description        | Status   |
| ------------------ | -------- |
| [CPP analyzer]  | [Complete] |
| [Documentation Refactor]  | [Complete] |



---
## Next week goals
- complete C# analyzer
- work out aggregation issues

### Extra Details:

<details>
  This week I set out to create the CPP analyzer and the C# analyzer, I unfortunately did not complete the C# analyzer and factored in my documentation refactoring for this week.  While the C# analyzer didnt get done due to a combination of unfortunate circumstances (personal will not elaborate) and some poor planning on my part to account for the situations I have figured out that the CPP analyzer should be able to account for C# with a few modifications using tree_sitter, which was a neat tool I found while doing somemore research on what to use! so it should be a quick set up for the next week. furthermore, the CPP analyzer is unfortunately not connected to the main system at the moment since we discovered a potential refactor we have to look into in our aggregation and output functions which will be discussed and reworked in the following weeks to not only be compadible with fast API but also with the new front end.


</details>


## Dates of Sprint: (1/4/2026 – 1/11/2026)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src= "https://github.com/COSC-499-W2025/capstone-project-team-2/blob/Cameron-Personal-Logs/docs/logs/peer_eval_screenshots/PL_Cameron_1-9-2026.png" />


### Features Worked on this Milestone (Provide sufficient detail)
  * #1: Refactor C anlyzer 


## Associated Tasks from Project Board:

| Description        | Status   |
| ------------------ | -------- |
| [Refactor C file analyzer]  | [Complete] |



---
## Next week goals
- complete documentation write up
---

### Extra Details:

<details>
  This week I set out to refactoring the C analyzer, I initiated some of the refactoring prior to the break but during the week I reworked a few sections and ensured it was compadible with the refactoring done by fellow teammates before merging it with the base project. the original analyzer had alot of errors when it came to formatting and calculations. the corrections were made included creating an entirely seperate aggregator for C specific language  as well as some small language detectors to change between file designations so propper aggregation can be done per file.


</details>

## Dates of Sprint: (12/1/2025 – 12/7/2025)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src= "https://github.com/COSC-499-W2025/capstone-project-team-2/blob/Cameron-Personal-Logs/docs/logs/peer_eval_screenshots/PL_Cameron_12-5-25.png" />


### Features Worked on this Milestone (Provide sufficient detail)
  * #1: Create a C file analyzer


## Associated Tasks from Project Board:

| Description        | Status   |
| ------------------ | -------- |
| [Create a C file analyzer]  | [Complete] |



---
## Next week goals
- work out refacting over break
---

### Extra Details:

<details>
Worked on creating a new section to our code analysis, i created a subsection for C coding as well as an appropriate test for the analysis as a whole which then was directly integrated with the project menu for use in portfolio and resume items. it was a rather large PR, however, it was nessesary for this week given I unfortunately didnt have time to reduce the ammount of lines required due to essays, and tests and final exams this friday and the upcoming monday. I did find an alternative way to run the analysis about 3/4s of the way to completion which i plan to use in a refactorization of the code at a later date.

</details>



## Dates of Sprint: (11/24/2025 – 11/30/2025)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src= "https://github.com/COSC-499-W2025/capstone-project-team-2/blob/Cameron-Personal-Logs/docs/logs/peer_eval_screenshots/CameronG_PL_11-29-25.png" />


### Features Worked on this Milestone (Provide sufficient detail)
  * #1: Create/Format portfolio output
  * #2: Add Ollama LLM to docker


## Associated Tasks from Project Board:

| Description        | Status   |
| ------------------ | -------- |
| [Create/Format portfolio output]  | [Complete] |
| [Add Ollama LLM to docker]  | [Complete] |



---
## Next week goals
- Discuss next steps with team
---

### Extra Details:

<details>
This week i added portfolio output to our user interface, I also added our selected LLM Olama to our docker instance for future use of our LLM. Overall I did a small piece of critial work. the integration of Ollama into docker reduces our need to export data to an online enviroment by keeping it built into our project. furthermore, we had yet to have a formal output for our resume and portfolio. I was hoping to do more this week but a combination of a miscommunication between my team partner and I led me to do less on top of the fact that I really needed to focus on the final assignments/projects for my other classes.

</details>


## Dates of Sprint: (11/10/2025 – 11/22/2025)

### Peer Eval Screenshot:

<img width="1092" height="626" alt="image" src= "https://github.com/COSC-499-W2025/capstone-project-team-2/blob/Cameron-Personal-Logs/docs/logs/peer_eval_screenshots/PL_Cameron_11-22-25.png" />


### Features Worked on this Milestone (Provide sufficient detail)
  * #1: Create Database


## Associated Tasks from Project Board:

| Description        | Status   |
| ------------------ | -------- |
| [Establish automated test on docker]  | [Complete] |



---
## Next week goals
The goals for Week 6:
- Automate Docker launch
- integrate all features for demo
---

### Extra Details:

<details>
So over the break and this week I worked on docker/sql functions. over the reading break I created the helper function for deletion, loading, as well as an update method that allows for us to syncronize json files and content. This week I created a function for the docker containers that run all our tests before hand. What I plan on doing next is creating an automization to launch docker if not already, as well as possibly to establish a docker container if no container was already there

</details>


## Dates of Sprint: (11/2/2025 – 11/8/2025)

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
So I set out this week to set up the database and edit the functions i set up last week to properly use mysql. Of which i completed and now can create the database and all appropriate tables. I really wanted to set up helper functions so that way we can just call those methods and it pulls data types, uploads the files,etc this week but i struggled with two things. A delay in my inital PR this week being merged (this is on me) as well as struggling with the mysql connection. I struggled particularily hard with getting the connection up and going between verision mismatches, ports and then docker set up changing a bit due to the win32 security import when it is built. after solving these issues I managed to get the task done. but i will be working hard over the reading break to ensure i get everything i want done and then some to make up for the unfortunate trouble shooting that i needed to do with SQL and Docker

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
