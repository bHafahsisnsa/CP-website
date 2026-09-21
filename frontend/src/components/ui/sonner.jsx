import { useTheme } from "next-themes"
import { Toaster as Sonner, toast } from "sonner"

const Toaster = ({
  ...props
}) => {
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      theme={theme}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-[color:var(--cp-paper-warm)] group-[.toaster]:text-[color:var(--cp-ink)] group-[.toaster]:border group-[.toaster]:border-[color:var(--cp-brass)]/35 group-[.toaster]:rounded-2xl group-[.toaster]:shadow-[0_20px_46px_-18px_rgba(38,28,14,0.35)]",
          title: "group-[.toast]:text-[color:var(--cp-ink)] group-[.toast]:font-semibold",
          description: "group-[.toast]:text-black/55",
          actionButton:
            "group-[.toast]:bg-[color:var(--cp-ink)] group-[.toast]:text-[color:var(--cp-paper)] group-[.toast]:rounded-full",
          cancelButton:
            "group-[.toast]:bg-black/5 group-[.toast]:text-black/60 group-[.toast]:rounded-full",
          closeButton:
            "group-[.toast]:bg-[color:var(--cp-paper)] group-[.toast]:border-black/10 group-[.toast]:text-black/50",
        },
      }}
      {...props} />
  );
}

export { Toaster, toast }
