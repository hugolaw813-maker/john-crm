# Sarah CRM Onboarding & Usage Guide

## Purpose
This guide explains how Sarah should use the CRM to:

1. **Add and update client data**
2. **Keep John’s meeting schedule / meeting records organized**
3. **Manage John’s tasks**

This is written as an everyday operating guide, not a technical manual.

---

# 1. CRM Overview

## Main Areas Sarah Will Use

### **People**
Use this for individual people:
- clients
- prospects
- agents
- referral partners
- professionals
- contacts

**This is the main source of truth.**
Everything should relate back to a **Person** whenever possible.

### **Companies**
Use this for:
- households
- businesses
- organizations
- offices
- family groupings

A Person can be connected to a Company/Household.

### **Tasks**
Use this for John’s action items and follow-ups.

Tasks should include:
- what needs to be done
- who it is for
- who it is assigned to
- due date
- priority/status

### **Deals**
This area still exists, but the important relationship field is now **Person**.
If Sarah is told to work in Deals, use the **Person** field as the first/main reference.

### **Conversations / Meeting Records**
Use this for calls, meetings, discussions, follow-ups, and meeting notes.

This is the best place to store:
- meeting summaries
- call notes
- follow-up dates
- discussion outcomes

---

# 2. Core Data Rule

## Golden Rule
Whenever possible, start with the **Person** record.

That means:
- Tasks should relate to a **Person**
- Conversations should relate to a **Person**
- Notes should relate to a **Person**
- Companies/Households are supporting records, not the main working record

If Sarah is unsure where to put something, the safest answer is:
> Put it under the correct **Person** first.

---

# 3. Logging In

Use the CRM link provided by John.

Current app URL:
- `http://172.31.153.173:3001`

If Sarah has login credentials, she should sign in normally.

---

# 4. How Sarah Should Enter Client Data

## A. Before Creating a New Person
Always search first.

### Search for:
- full name
- phone number
- email address
- company/household name

This avoids duplicates.

---

## B. When to Create a **Person**
Create a **Person** record when the individual is:
- a client
- a lead/prospect
- a spouse
- a child tied to planning/application work
- a professional contact
- an agent/referral contact

---

## C. Standard Fields Sarah Should Fill In for People
When creating or updating a Person, fill in as much of this as possible:

### Required / Most Important
- **Name**
- **Type**
- **Company** (household or organization, if applicable)

### Strongly Recommended
- **Email**
- **Phone**
- **Address**
- **Job Title**
- **Description**

---

## D. How to Use the **Type** Field
Use the best match:
- **Client** → existing client
- **Agent** → agent / insurance / advisor contact
- **CIO** → center of influence
- **BNI** → BNI networking contact
- **Professional** → attorney / CPA / business professional / etc.
- **Contact** → general contact if none of the above fit

### Rule of thumb
If this is a household/client John actively works with, use:
- **Client**

---

## E. What Goes in **Description**
Use Description for quick context that helps John immediately understand who this is.

Examples:
- “Retirement planning client, referred by Mike”
- “Jessica’s oldest son — college account setup”
- “CPA partner — possible referral source”
- “Needs life insurance follow-up after underwriting”

Keep it short and useful.

---

# 5. How Sarah Should Use **Companies / Households**

## When to Create a Company/Household
Create a Company record when there is:
- a family household
- a business entity
- an office/company
- an organization tied to multiple people

## What the Company record is for
Company/Household records are mainly for grouping.

Examples:
- husband + wife + children under one household
- multiple contacts under one business
- all related notes tied to one family/entity

## Best practice
Create or update the **Person** first, then link them to the correct **Company**.

---

# 6. How Sarah Should Enter Meeting Schedule / Meeting Records

## Important distinction
The CRM is best used to track:
- scheduled meetings
- completed meetings
- meeting notes
- follow-up dates

If there is a separate calendar system, that may still be the actual master calendar.

In the CRM, Sarah should use meeting/conversation records to capture the client-facing history and follow-up.

---

## A. When Sarah Should Create a Meeting Record
Create a record when:
- John has a scheduled client meeting/call
- John completed a meeting and notes need to be entered
- a follow-up conversation needs tracking
- a meeting outcome needs to be documented

---

## B. Fields to Fill for Meeting / Conversation Records
Use these fields when available:
- **Client** → link to the Person
- **Household** → link to Company/Household if relevant
- **Date** → meeting/call date
- **Type** → meeting / call / follow-up type
- **Status** → planned / completed / follow-up status
- **Summary** → short summary
- **Details** → fuller notes
- **Duration** → if known
- **Follow-up Date** → when John should revisit it

---

## C. How to Write Good Meeting Summaries
A good summary is short and readable in one line.

Examples:
- “Reviewed retirement rollover options and next steps”
- “Discussed children’s account setup and forms needed”
- “Follow-up on underwriting requirements and questionnaire”

## D. How to Write Good Meeting Details
Use Details for the full note.

Suggested format:
- reason for meeting
- what was discussed
- decisions made
- documents needed
- next step
- owner of next step

Example:
- Reviewed retirement contribution options for 2025.
- Client wants to move forward after receiving form number.
- Need to send follow-up materials.
- John to call carrier.
- Sarah to prepare documents.

---

## E. If a Meeting Creates Work
If a meeting produces an action item, Sarah should also create a **Task**.

### Rule:
**Conversation/Meeting record = what happened**
**Task = what needs to happen next**

---

# 7. How Sarah Should Manage John’s Tasks

## A. What belongs in Tasks
Use Tasks for action items such as:
- forms to send
- paperwork to process
- follow-up calls
- account openings
- document collection
- reminders after meetings
- application fixes
- anything John or Sarah needs to do next

---

## B. Task Fields Sarah Should Fill In
Every task should have:
- **Task description**
- **Person**
- **Assigned to**
- **Due date** (if known)
- **Status** = High / Medium / Low

### Meaning of fields
- **Person** = who the task is about
- **Assigned to** = which person in the People list is responsible / tied to execution
- **Due date** = when it should be completed
- **Status** = priority level

---

## C. How to Write a Good Task Title
Task names should start with the action.

Good examples:
- “Send life insurance questionnaire to Michael Razzano”
- “Open Roth account for Matthew Chan”
- “Prepare BNI presentation for Tuesday meeting”
- “Call carrier and confirm contribution form number for Anna Kim”

Avoid vague titles like:
- “Follow up”
- “Call client”
- “Forms”

The task title should be understandable without opening the record.

---

## D. How Sarah Should Use High / Medium / Low

### **High**
Use for:
- urgent client deadlines
- same-day / next-day action
- paperwork blocking progress
- tasks John specifically wants prioritized

### **Medium**
Use for:
- normal active work
- important follow-ups with no immediate emergency
- tasks that should move this week

### **Low**
Use for:
- non-urgent reminders
- longer-term follow-up
- nice-to-do items
- prep items without immediate deadline

---

## E. When Sarah Should Mark a Task Complete
Mark complete only when the action is actually done.

Examples:
- document sent
- account opened
- call completed
- issue resolved
- requested follow-up delivered

If part of the work is done but more remains:
- either leave task open
- or complete it and create a new next-step task

---

# 8. Daily Workflow for Sarah

## Start of Day
1. Open **Tasks**
2. Review **High** priority items first
3. Check due dates for today / overdue items
4. Open relevant **People** records as needed
5. Review recent meetings/conversations if needed

## During the Day
For every new piece of information:
- update the **Person** record
- log any important meeting/call notes
- create or update a **Task**

## End of Day
1. Mark completed tasks done
2. Add notes to any meetings that happened
3. Add follow-up dates where needed
4. Make sure new client info is attached to the right Person

---

# 9. Best Practices

## 1. Search before creating
Always check for an existing Person or Company first.

## 2. Person first
If unsure where something belongs, start with the Person record.

## 3. Keep task names specific
A task should say exactly what needs to happen.

## 4. Keep notes useful
Write notes so John can understand them later without guessing.

## 5. Use Company only as support structure
Company/Household is for grouping. Person is the main working record.

## 6. Convert conversation into action
If a meeting creates follow-up work, create a task right away.

## 7. Don’t leave fields vague if Sarah already knows the answer
If Sarah knows the client type, due date, or summary, enter it.

---

# 10. Data Entry Standards

## Names
Use real full names when known.

### Good:
- Michael Razzano
- Jessica Lee
- Matthew Chan

### Avoid:
- Mike maybe
- Jess?
- Household only, when a real person is known

---

## Phone Numbers
Use a clean standard format if possible.
Example:
- (555) 123-4567
- 555-123-4567

## Emails
Use the real client email, not placeholders, when known.

## Addresses
Put mailing/home address in Address when relevant.

## Notes
Avoid overly cryptic notes.
Write what John will actually need later.

---

# 11. Example Scenarios

## Example 1: New Client Meeting Scheduled
Sarah receives notice John will meet Michael Razzano on Tuesday.

### Sarah should:
1. Search **Michael Razzano** in People
2. Update Person record if needed
3. Create or update a **Conversation/Meeting** record
   - Client = Michael Razzano
   - Date = Tuesday
   - Status = scheduled/planned
   - Summary = “Retirement planning review”
4. Create any prep **Task** if needed
   - Example: “Prepare forms for Michael Razzano meeting”

---

## Example 2: After a Client Call
John finishes a call and tells Sarah:
- client needs questionnaire sent
- follow-up next Thursday

### Sarah should:
1. Open the Person record
2. Add/update the meeting/conversation note
3. Create a Task:
   - “Send questionnaire to [Client Name]”
4. Set due date
5. Set priority
6. Add follow-up date in the meeting/conversation record

---

## Example 3: New Household
A husband and wife become clients.

### Sarah should:
1. Create a Company/Household record if needed
2. Create a Person record for each spouse
3. Link both People to the Company/Household
4. Add notes/tasks under the relevant Person
5. Use the household link only for grouping

---

# 12. What Sarah Should Avoid

Do **not**:
- create duplicate People because of spelling variation
- store a person only as a household if the real individual is known
- use vague task names
- leave a meeting undocumented if it matters
- create tasks with no linked Person when a Person is known
- rely only on memory instead of entering the note/task

---

# 13. Recommended Operating Rule for Sarah

If Sarah only remembers one rule, it should be this:

> **Every client-related item should connect back to the correct Person.**

That includes:
- client data
- meeting notes
- follow-ups
- tasks

---

# 14. Quick Reference Cheat Sheet

## Use **People** for:
- client profile
- contact details
- type
- core relationship record

## Use **Companies** for:
- household / family / business grouping

## Use **Tasks** for:
- action items
- follow-ups
- deadlines
- priority tracking

## Use **Conversations / Meeting Records** for:
- call notes
- meeting summaries
- follow-up dates
- discussion history

---

# 15. Suggested Training Flow for Sarah

## Day 1
- learn People
- learn how to search before creating
- learn Tasks

## Day 2
- practice updating client records
- practice entering meeting notes
- practice linking tasks to the right person

## Day 3
- independently process a full workflow:
  - update Person
  - log meeting
  - create follow-up task

---

# 16. Final Standard

Sarah’s work is done correctly when:
- client information is accurate
- the right Person record exists
- meetings are documented
- next steps are in Tasks
- John can open the CRM and instantly understand:
  - who the client is
  - what happened
  - what needs to happen next

---

If needed, this guide can be expanded into a shorter **Sarah Quick Start Checklist** and a separate **Admin SOP** later.
