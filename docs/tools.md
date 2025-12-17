# Tools

This document describes the function tools exposed by PharmAI. These tools are the **only authoritative source** of demo medication and user data.



## General Conventions

- All tools return JSON.
- All tools return an `ok` boolean:
  - `ok: true` indicates success.
  - `ok: false` indicates an error with an `error_code`.
- The demo UI selects the `user_id` via a dropdown.  
  The agent **must not guess or invent** a user.
- Tools are defined using **Responses API strict mode**:
  - `strict: true`
  - `additionalProperties: false`
  - All parameters are required (nullable values represent optional inputs).



## Error Codes

Tools may return the following error codes:

- `MISSING_MEDICATION_QUERY` – no medication text provided
- `MED_NOT_FOUND` – medication not found in demo DB
- `MISSING_USER_ID` – no demo user selected
- `USER_NOT_FOUND` – unknown demo user ID

The system prompt defines how the agent must respond to each error (ask one clarifying question, stop, or show a message).



## Tool: get_medication

### Purpose

Fetch **factual medication information** from the demo database.  
This is the **only allowed source** of medication facts.

This includes:
- Active ingredients
- Warnings
- Dosage text
- Prescription requirement
- Stock status



### Inputs

- `query` (string, required)  
  Medication name, brand, alias, or a sentence containing it.



### Output

On success:
- `ok`: true
- `med`:
  - `medication_id`
  - `name` (display name)
  - `brand_name`
  - `generic_name`
  - `active_ingredients`
  - `form`
  - `strength`
  - `requires_prescription`
  - `in_stock`
  - `dosage_instructions`
  - `warnings`

On error:
- `ok`: false
- `error_code`



### Example (Success)

ok: true  
med:  
- medication_id: m003  
- name: Advil (Ibuprofen) 200mg  
- brand_name: Advil  
- generic_name: Ibuprofen  
- active_ingredients: ["Ibuprofen"]  
- form: tablet  
- strength: 200mg  
- requires_prescription: false  
- in_stock: true  
- dosage_instructions: Take as directed on the label.  
- warnings: Do not use if you have...



### Agent Behavior

- If the query is missing → ask **one** clarifying question: “Which medication?”
- If the medication is not found → inform the user and optionally offer to list available medications
- If a requested field is missing → say “Not available in the demo database.”



## Tool: get_user_prescriptions

### Purpose

Return the selected demo user’s prescriptions as medication summaries.

This tool is used to answer:
- “What are my prescriptions?”
- “Do I have a prescription for X?” (combined with get_medication)



### Inputs

None.  
The server injects the selected demo `user_id`.



### Output

On success:
- `ok`: true
- `user`:
  - `user_id`
  - `full_name`
- `prescriptions`: list of medication summaries
  - `medication_id`
  - `brand_name`
  - `generic_name`
  - `strength`
  - `rx_required`
  - `in_stock`
  - `display_name`

On error:
- `ok`: false
- `error_code`



### Example (Success)

ok: true  
user:  
- user_id: u001  
- full_name: Noa Cohen  

prescriptions:
- Zoloft (Sertraline) 50mg



### Agent Behavior

- If no user is selected → prompt the user to choose one from the dropdown and stop.



## Tool: list_medications

### Purpose

List medications available in the demo pharmacy database.

Supports optional filtering by:
- Prescription requirement
- Stock status



### Inputs

- `rx_filter` (string or null, required)
  - rx
  - non_rx
  - both
  - null (defaults to both)

- `stock_filter` (string or null, required)
  - in_stock
  - out_of_stock
  - both
  - null (defaults to both)



### Output

On success:
- `ok`: true
- `medications`: list of medication summaries
  - `medication_id`
  - `brand_name`
  - `generic_name`
  - `strength`
  - `rx_required`
  - `in_stock`
  - `display_name`



### Example (Success)

ok: true  
medications:
- Advil (Ibuprofen) 200mg
- Tylenol (Acetaminophen) 500mg



### Agent Behavior

- If no medications match the filters → inform the user that no results were found.
- If the user asks for more details → follow up with get_medication.



## Tool Interaction Rules

- Medication facts must **always** come from get_medication.
- To answer “Do I have a prescription for X?”:
  1. Call get_user_prescriptions
  2. Call get_medication to resolve the canonical medication_id
  3. Compare medication_id values
- Tool outputs are authoritative and must not be paraphrased or supplemented.