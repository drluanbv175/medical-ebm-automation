export function WorkflowChecklist({ steps }: { steps: { label: string; done: boolean; note?: string }[] }) {
  return (
    <ul className="workflow">
      {steps.map((step) => (
        <li key={step.label}>
          <span className={`dot ${step.done ? "done" : "todo"}`} />
          <div>
            <strong>{step.label}</strong>
            {step.note ? <div className="eyebrow">{step.note}</div> : null}
          </div>
        </li>
      ))}
    </ul>
  );
}
