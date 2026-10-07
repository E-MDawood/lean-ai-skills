# Quality assessment (Phase 2)

Score the business material on each dimension, then give an overall verdict. Use evidence counts, not impressions: "14 of 16 use cases have data tables", "6 fields sent to partners have no input source".

| Dimension | Good | Poor |
|---|---|---|
| **Completeness** | Every use case has actors, main flow, alternatives, rules, messages and data tables | Stories are one-liners; no data definitions; appendices referenced but missing |
| **Consistency** | Same field, same name, same codes everywhere | The same value has several names or codes; status lists differ between tables |
| **Precision** | Rules give numbers, conditions and error messages | "Handle appropriately", "as needed", "to be decided" |
| **Traceability** | Rules and tables have IDs that other parts cite | No IDs; rules buried in prose |
| **Terminology** | Terms defined once and used consistently | Undefined acronyms; one concept with several names |
| **Data lineage** | Every outbound field has an inbound source | Fields sent to partners that nobody ever provides |
| **Contradictions** | None, or few and minor | Rules that cannot both be true |
| **Inputs available** | Stories, BRD, appendices, attachments, plan | Key inputs missing or unreadable |

## Verdict

- **Good**: most dimensions good; gaps are edge cases. The primer is reliable; say so.
- **Mixed**: usable but with named weak areas. List them in chat and in the Open points tab.
- **Poor**: several dimensions poor, or contradictions in core flows, or most data undefined.

For **Poor**, say this explicitly to the user, in these terms or very close:

> The business material is poor. A lot of points need clarification and resolution from the business, and the artifact cannot be very reliable at this stage. It can only be used as a starting point to categorize the business visually so you can check it quickly.

Then:
- Put a visible warning banner at the top of the artifact with the same message and the date.
- Mark uncertain content in the artifact (for example a "Unconfirmed" pill) instead of presenting guesses as facts.
- Make the Open points tab prominent, and list the top blockers first.
- Recommend getting the business answers before using the primer for estimates or design.

Never soften a poor verdict to be agreeable. Re-assess and update the banner when the business answers questions.
