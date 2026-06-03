export default function PageHeader({ title, subtitle, children }) {
  return (
    <div className="px-8 py-6 border-b border-dark-600 flex items-center justify-between">
      <div>
        <h1 className="text-xl font-bold text-white">{title}</h1>
        {subtitle && <p className="text-slate-400 text-sm mt-0.5">{subtitle}</p>}
      </div>
      {children && <div className="flex items-center gap-3">{children}</div>}
    </div>
  )
}
