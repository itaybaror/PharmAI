# Evaluation Plan

### Disclaimer

PharmAI is designed to handle **many different user workflows** and follow-up patterns.  
The agent is robust, context-aware, and capable of resolving a wide range of multi-step interactions.

The workflows described in this document are **representative examples** chosen to best demonstrate:
- Multi-step reasoning
- Tool usage across turns
- Context retention
- Correct scoping of responses

They are **not** an exhaustive list of all supported flows.



## Evaluation Goals

The goal of this evaluation is to verify that PharmAI:

- Correctly identifies user intent at each step
- Uses the appropriate tools when authoritative data is required
- Maintains conversational context across multiple turns
- Produces scoped, accurate responses without hallucinating information
- Handles follow-up questions naturally and deterministically

Each flow below represents a realistic pharmacy interaction a user might have.



## Flow 1: Prescription Review → Stock Status → Warnings

### User Goal
Review current prescriptions, check availability, and understand safety information.

### Expected Behavior
The agent should maintain context across turns and use tools incrementally as new information is requested.

### Step-by-Step Flow

1. **User:**  
   *“What are my prescriptions?”*

   **Agent Actions:**
   - Detects a prescription list request
   - Calls `get_user_prescriptions`
   - Returns the list of prescribed medications (names only)

2. **User:**  
   *“Are they in stock?”*

   **Agent Actions:**
   - Resolves “they” to the previously listed prescriptions
   - Calls `get_medication` for each medication
   - Responds with stock status only

3. **User:**  
   *“Do they have any warnings?”*

   **Agent Actions:**
   - Maintains conversational context
   - Calls `get_medication` as needed
   - Returns warnings verbatim from the database
   - Does not add medical advice or interpretation

### Tools Used
- `get_user_prescriptions`
- `get_medication`

### Evaluation Criteria
- Correct resolution of pronouns (“they”)
- Proper tool usage at each step
- No hallucinated or inferred medical information
- Responses scoped strictly to the user’s question



## Flow 2: Medication Lookup → Prescription Requirement → Stock Status

### User Goal
Understand whether a medication requires a prescription and if it is available.

### Step-by-Step Flow

1. **User:**  
   *“Do I need a prescription for Advil?”*

   **Agent Actions:**
   - Calls `get_medication`
   - Returns prescription requirement only

2. **User:**  
   *“Is it in stock?”*

   **Agent Actions:**
   - Maintains context for the same medication
   - Uses existing or repeated `get_medication` call
   - Returns stock status only

### Tools Used
- `get_medication`

### Evaluation Criteria
- Context retention across turns
- Correct field-level response selection
- No extra explanation beyond requested data



## Flow 3: Inventory Discovery → Follow-Up Filtering

### User Goal
Explore what medications are available in the pharmacy.

### Step-by-Step Flow

1. **User:**  
   *“What medications do you have?”*

   **Agent Actions:**
   - Calls `list_medications`
   - Returns medication names only

2. **User:**  
   *“Which ones require a prescription?”*

   **Agent Actions:**
   - Calls `list_medications` with `rx_filter=rx`
   - Returns filtered results

### Tools Used
- `list_medications`

### Evaluation Criteria
- Correct use of filter parameters
- Accurate inventory listing
- Clean, readable output



## General Evaluation Checks

Across all flows, the following must always hold true:

- The agent never invents data
- All medication facts come exclusively from tools
- Tool failures are handled gracefully and clearly
- The agent responds in the user’s language
- Streaming responses appear incrementally and naturally



## Success Criteria

The agent is considered successful if it:

- Completes all flows without errors
- Uses tools deterministically and correctly
- Maintains conversational context across turns
- Produces clear, scoped, and accurate responses



## Notes for Reviewers

While PharmAI is designed to be robust and capable of handling a wide range of conversational flows, it is intentionally **limited to the requirements defined in this assignment** and to the **synthetic data provided in the sample database**.

The workflows presented here are representative examples that demonstrate how the agent:
- Follows multi-step conversations within a constrained domain
- Uses tools deterministically to access authoritative data
- Maintains context across turns while respecting strict behavioral rules

PharmAI does not attempt to generalize beyond:
- The supported tool set
- The demo users and medications in the database
- The explicitly defined capabilities in the system prompt
