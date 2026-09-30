---
name: forms
description: "Use this skill when the user asks to create, edit, or fix any form in the project. Covers new form creation, field additions, validation changes, multi-step forms, view modes, and form hook structure using react-hook-form and RenderFormFields."
---

# Forms Skill

> **Scope**: Use this skill for **any change involving forms** — new forms, edits, additions, or bug fixes.
> When modifying an existing form, follow the pattern already in use (Pattern 1 or Pattern 2) unless explicitly asked to change it.

---

## Overview

Forms in this project are built on **react-hook-form** with a layered component system living in `src/shared/components/Form/`. There are two main patterns — pick the one that fits the situation.

---

## Pattern 1: Declarative Field Config (preferred for new forms)

Use `RenderFormFields` with a `fields` array. This handles rendering, view mode, loading states, and label resolution automatically.

```tsx
import RenderFormFields from "@/shared/components/Form/Render/RenderFormFields";
import { RenderFormField } from "@/shared/components/Form/Render/types";
import { useForm } from "react-hook-form";

type MyFormValues = {
  name: string;
  role: string;
};

const fields: RenderFormField<MyFormValues>[] = [
  { name: "name", fieldType: "text" },
  { name: "role", fieldType: "dropdown", options: roleOptions },
];

// Edit mode
<RenderFormFields fields={fields} form={form} />

// View mode
<RenderFormFields fields={fields} form={form} isInViewMode />

// View mode with raw values (no form instance needed)
<RenderFormFields fields={fields} values={data} isInViewMode />
```

### Available Field Types

| `fieldType`           | Component used            | Extra props                                                                   |
| --------------------- | ------------------------- | ----------------------------------------------------------------------------- |
| `"text"`              | FormTextInput             | —                                                                             |
| `"number"`            | FormTextInput             | —                                                                             |
| `"description"`       | FormTextInput (multiline) | —                                                                             |
| `"mobile"`            | FormPhoneInput            | —                                                                             |
| `"dropdown"`          | FormSelectInput           | `options`, `loading`, `renderOption`                                          |
| `"dropdown-multiple"` | FormSelectInput           | `options`, `loading`, `renderOption`                                          |
| `"checkboxes"`        | FormCheckboxesInput       | `options`, `loading`, `noOptionsText`, `renderOption`                         |
| `"radio"`             | FormRadio                 | `options`, `valueMode: "primitive" \| "lookup"`                               |
| `"yes-no"`            | FormYesNoInput            | —                                                                             |
| `"date"`              | FormDatePicker            | `minDate`, `maxDate`, `clearable`, `disableHijri`, `withCalendarIcon`         |
| `"file"`              | FormDropFileInput         | `maxSize`, `accept`, `inputType`, `enableInstantStorageUpload`, `renderInput` |
| `"file-multiple"`     | FormDropFileInput         | same as file + `maxFiles`                                                     |
| `"custom"`            | your render fn            | `keyName` (required), `render: (options) => ReactNode`                        |

### Common Field Config Options

```ts
{
  name: "fieldName",          // Path<T> — required
  fieldType: "text",          // required
  optional: true,             // default: required
  label: "Override Label",    // default: auto from t(field.name)
  description: "...",
  placeholder: "...",
  className: "col-span-2",    // Tailwind classes for the field container
  disabled: false,
  hidden: false,
  hint: "Helper text",
  loading: false,
  viewOnly: true,             // always renders in view mode
  isForViewModeOnly: true,    // hidden in edit mode
  isForEditModeOnly: true,    // hidden in view mode
  renderViewOnlyValue: (value) => <CustomDisplay value={value} />,
}
```

### Dynamic fields (computed from form state)

```ts
const fields: RenderFormField<MyFormValues>[] = [
    ({ form }) => ({
        name: "conditionalField",
        fieldType: "text",
        hidden: form?.watch("role") !== "admin"
    })
];
```

---

## Pattern 2: Individual Form Input Components

Use when you need fine-grained control or are building a custom layout that `RenderFormFields` doesn't fit.

Each input type has two layers:

-   `App{Input}` — pure UI, no form binding
-   `Form{Input}` — wraps `App{Input}` with `Controller` from react-hook-form

```tsx
import FormTextInput from "@/shared/components/Form/Inputs/TextInput/FormTextInput";
import FormSelectInput from "@/shared/components/Form/Inputs/SelectInput/FormSelectInput";

<FormTextInput name="name" form={form} label="Full Name" required />
<FormSelectInput name="role" form={form} options={roleOptions} required />
```

Available `Form*` components:

-   `FormTextInput` — text, number, multiline
-   `FormPhoneInput` — mobile/phone
-   `FormSelectInput` — single or multiple dropdown
-   `FormCheckboxesInput` — checkbox group
-   `FormRadio` — radio group
-   `FormYesNoInput` — yes/no toggle
-   `FormDatePicker` — date picker (supports Hijri)
-   `FormDropFileInput` — file upload (single or multiple)

---

## Multi-Step Forms

Use `AppMultiStepForm` for wizard-style flows.

```tsx
import AppMultiStepForm from "@/shared/components/Form/AppMultiStepForm/AppMultiStepForm";
import { MultiStepFormStep } from "@/shared/components/Form/types";

const steps: MultiStepFormStep[] = [
    {
        label: t("step1Label"),
        content: <Step1Fields form={form} />,
        validate: async () => {
            const valid = await form.trigger(["field1", "field2"]);
            return valid;
        }
    },
    {
        label: t("step2Label"),
        content: <Step2Fields form={form} />
    }
];

<AppMultiStepForm
    form={form}
    steps={steps}
    onSubmit={handleSubmit}
    onSaveDraft={handleDraft} // optional
    onCancel={handleCancel} // optional
/>;
```

---

## Form Actions Layout

For custom submit/cancel button arrangements, use `FormActionLayout`:

```tsx
import FormActionLayout from "@/shared/components/Form/Actions/FormActionLayout";

<FormActionLayout
    StartButton={<Button onClick={onCancel}>Cancel</Button>}
    EndSubButton={<Button onClick={onDraft}>Save Draft</Button>}
    EndMainButton={<Button type="submit">Submit</Button>}
/>;
```

---

## Type Patterns

```ts
import { CommonInputProps, CommonFormInputProps } from "@/shared/components/Form/types";

// For a new App-level input component:
type MyInputProps = CommonInputProps<MuiComponentProps, { extraProp: string }>;

// For a new Form-level input component:
type MyFormInputProps<T extends FieldValues> = CommonFormInputProps<MyInputProps, T>;
```

---

## Labels & Translations

`RenderFormFields` automatically resolves labels via `t(field.name)`. This means the translation key must exist in both `en/translation.ts` and `ar/translation.ts` with the same key path as the field `name`. Only provide an explicit `label` prop if the auto-resolved key is wrong for this context.

---

## Form Hooks Convention

Forms are typically split into **three dedicated hooks**, each with a single responsibility. Follow this pattern for any non-trivial form.

---

### 1. `use{Feature}FormSchema` — Validation schema

Owns the Zod schema and (for multi-step forms) the list of fields to validate per step.

```ts
// hooks/useMyFeatureFormSchema.ts
import useCommonSchemas from "@/hooks/app/useCommonSchemas";
import { z } from "zod";

const useMyFeatureFormSchema = () => {
    const { requiredStrings, requiredLookUp, requiredDate } = useCommonSchemas();

    const schema: z.ZodType<MyFormValues> = z.object({
        name: requiredStrings.common,
        role: requiredLookUp,
        startDate: requiredDate
    });

    // For multi-step forms, export field paths per step for trigger() calls
    const stepValidationFields = {
        step1: ["name"] as Path<MyFormValues>[],
        step2: ["role", "startDate"] as Path<MyFormValues>[]
    };

    return { schema, stepValidationFields };
};
```

**Always use `useCommonSchemas`** for reusable primitives — do not re-define common validators inline:

| Primitive                                              | Use for                       |
| ------------------------------------------------------ | ----------------------------- |
| `requiredStrings.common`                               | Required text                 |
| `requiredStrings.name` / `requiredStrings.description` | With max-length               |
| `requiredLookUp`                                       | Lookup objects `{ id, name }` |
| `optionalLookUp`                                       | Optional lookup               |
| `requiredDate` / `optionalDate`                        | Date fields                   |
| `requiredEmail`                                        | Email with format validation  |
| `requiredPhoneNumber`                                  | Phone with format validation  |
| `requiredFileWithStorageKey`                           | File upload with storage key  |
| `requiredNumber`                                       | Numeric fields                |
| `requiredContactInfoSchema`                            | Full contact info block       |

---

### 2. `use{Feature}FormFields` — Field definitions

Owns all `RenderFormField` config arrays. Loads option lists, applies layout classes, builds field configs.

```ts
// hooks/useMyFeatureFormFields.ts
import useFormFieldsLayout from "@/hooks/common/useFormFieldsLayout";
import { RenderFormField } from "@/shared/components/Form/Render/types";

const useMyFeatureFormFields = () => {
    const { layout, fieldsGridClassName } = useFormFieldsLayout();

    const fields: RenderFormField<MyFormValues>[] = [
        { name: "name", fieldType: "text", className: layout.full },
        { name: "role", fieldType: "dropdown", options: roleOptions, className: layout.half },
        { name: "startDate", fieldType: "date", className: layout.half }
    ];

    return { fields, fieldsGridClassName };
};
```

**Layout classes from `useFormFieldsLayout`:**

| Key              | Class           | Columns    |
| ---------------- | --------------- | ---------- |
| `layout.full`    | `col-span-full` | Full width |
| `layout.half`    | `col-span-6`    | Half       |
| `layout.third`   | `col-span-4`    | Third      |
| `layout.quarter` | `col-span-3`    | Quarter    |

Use `fieldsGridClassName` as the `className` on `RenderFormFields` when using a 12-col grid.

---

### 3. `use{Feature}Form` — Main orchestrator

Composes the schema and fields hooks, instantiates `useForm`, and returns everything the component needs.

```ts
// hooks/useMyFeatureForm.ts
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

const useMyFeatureForm = (initialData?: MyData) => {
    const { schema, stepValidationFields } = useMyFeatureFormSchema();
    const { fields, fieldsGridClassName } = useMyFeatureFormFields();

    const form = useForm<MyFormValues>({
        resolver: zodResolver(schema),
        mode: "all",
        defaultValues: buildDefaultValues(initialData)
    });

    return { form, fields, fieldsGridClassName, stepValidationFields };
};

export type UseMyFeatureFormReturn = ReturnType<typeof useMyFeatureForm>;
```

Always export the return type as `Use{Feature}FormReturn` — it's used for prop typing in child components.

---

### Default values

Extract `buildDefaultValues` into a separate **utility function** (not a hook) in a `utils/` file next to the hooks:

```ts
// utils/buildMyFeatureDefaultValues.ts
export const buildDefaultValues = (data?: MyData): Partial<MyFormValues> => ({
    name: data?.name ?? "",
    role: data?.role ?? null
});
```

---

## Checklist for New Forms

-   [ ] Define a typed `FormValues` type
-   [ ] Create `use{Feature}FormSchema` — Zod schema using `useCommonSchemas` primitives
-   [ ] Create `use{Feature}FormFields` — field configs using `useFormFieldsLayout` for layout classes
-   [ ] Create `use{Feature}Form` — orchestrator that composes schema + fields + `useForm` with `zodResolver`
-   [ ] Extract default values into a `buildDefaultValues` utility function
-   [ ] Export `Use{Feature}FormReturn` type from the main form hook
-   [ ] Use `RenderFormFields` with the fields array (preferred) or individual `Form*` components
-   [ ] Add translation keys to **both** en and ar files
-   [ ] Support view mode via `isInViewMode` if the form has a read-only state
-   [ ] Use `FormActionLayout` or `AppMultiStepForm` for action buttons
-   [ ] Never hardcode colors — use theme tokens
