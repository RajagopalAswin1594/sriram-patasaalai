export function PageHeader({ title, description }: { title: string; description?: string }) {
  return (
    <div className="mb-6">
      <h2 className="text-2xl font-semibold text-stone-900">{title}</h2>
      {description ? <p className="mt-1 text-sm text-stone-500">{description}</p> : null}
    </div>
  );
}
