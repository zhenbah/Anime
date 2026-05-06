import * as React from 'react';
import * as SelectPrimitives from '@radix-ui/react-select';
import { cn } from '@/lib/utils';
import { Check, ChevronDown } from 'lucide-react';

const Select = SelectPrimitives.Root;
const SelectGroup = SelectPrimitives.Group;
const SelectValue = SelectPrimitives.Value;

const SelectTrigger = React.forwardRef<
  React.ElementRef<typeof SelectPrimitives.Trigger>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitives.Trigger>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitives.Trigger
    ref={ref}
    className={cn(
      'flex h-10 w-full items-center justify-between rounded-lg border border-border bg-background px-3 py-2 text-sm',
      'hover:bg-muted/50 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
      'disabled:cursor-not-allowed disabled:opacity-50',
      className
    )}
    {...props}
  >
    {children}
    <SelectPrimitives.Icon asChild>
      <ChevronDown className="w-4 h-4 opacity-50" />
    </SelectPrimitives.Icon>
  </SelectPrimitives.Trigger>
));
SelectTrigger.displayName = SelectPrimitives.Trigger.displayName;

const SelectContent = React.forwardRef<
  React.ElementRef<typeof SelectPrimitives.Content>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitives.Content>
>(({ className, children, position = 'popper', ...props }, ref) => (
  <SelectPrimitives.Portal>
    <SelectPrimitives.Content
      ref={ref}
      className={cn(
        'relative z-50 min-w-[8rem] overflow-hidden rounded-lg border border-border bg-popover text-popover-foreground shadow-md',
        'data-[state=open]:animate-in data-[state=closed]:animate-out',
        'data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0',
        'data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95',
        'data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2',
        'data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
        className
      )}
      position={position}
      {...props}
    >
      <SelectPrimitives.Viewport className="p-1">
        {children}
      </SelectPrimitives.Viewport>
    </SelectPrimitives.Content>
  </SelectPrimitives.Portal>
));
SelectContent.displayName = SelectPrimitives.Content.displayName;

const SelectItem = React.forwardRef<
  React.ElementRef<typeof SelectPrimitives.Item>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitives.Item>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitives.Item
    ref={ref}
    className={cn(
      'relative flex w-full cursor-default select-none items-center rounded-md py-1.5 pl-8 pr-2 text-sm',
      'hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground',
      'outline-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
      className
    )}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <SelectPrimitives.ItemIndicator>
        <Check className="w-4 h-4" />
      </SelectPrimitives.ItemIndicator>
    </span>
    <SelectPrimitives.ItemText>{children}</SelectPrimitives.ItemText>
  </SelectPrimitives.Item>
));
SelectItem.displayName = SelectPrimitives.Item.displayName;

export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectItem,
};
