import { Dialog, DialogContent, DialogOverlay } from '@/components/ui/Modal';
import { cn } from '@/lib/utils';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
}

export function Modal({ isOpen, onClose, children, className }: ModalProps) {
  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogOverlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" />
      <DialogContent
        className={cn(
          'fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 glass rounded-2xl p-6 shadow-2xl',
          className
        )}
      >
        {children}
      </DialogContent>
    </Dialog>
  );
}
