import { Command as CommandPrimitive } from "cmdk"
import { X } from "lucide-react"
import * as React from "react"

import { Badge } from "@/components/ui/badge"
import { Command, CommandGroup, CommandItem, CommandList } from "@/components/ui/command"

type Option = {
  value: string
  label: string
}

interface FancyMultiSelectProps {
  selected: string[];
  onChange: (value: string[]) => void;
  options: Option[];
  placeholder?: string;
}

export function FancyMultiSelect({ selected, onChange, options, placeholder = "Select..." }: FancyMultiSelectProps) {
  const inputRef = React.useRef<HTMLInputElement>(null)
  const [open, setOpen] = React.useState(false)
  const [inputValue, setInputValue] = React.useState("")

  const handleUnselect = React.useCallback((tag: string) => {
    onChange(selected.filter((s) => s !== tag))
  }, [selected, onChange])

  const handleKeyDown = React.useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
    const input = inputRef.current
    if (input) {
      if (e.key === "Delete" || e.key === "Backspace") {
        if (input.value === "") {
          const newSelected = [...selected]
          newSelected.pop()
          onChange(newSelected)
        }
      }
      if (e.key === "Escape") {
        input.blur()
      }
      if (e.key === "Enter") {
        // Prevent form submission
        e.preventDefault(); 
        e.stopPropagation();

        // Allow creating new tags if not in options
        if (inputValue && !selected.includes(inputValue)) {
           // check if it matches an existing option first
           const existingOption = options.find(opt => opt.value === inputValue || opt.label === inputValue);
           const valueToAdd = existingOption ? existingOption.value : inputValue;
           
           if (!selected.includes(valueToAdd)) {
             onChange([...selected, valueToAdd]);
             setInputValue("");
           }
        }
      }
    }
  }, [selected, onChange, inputValue, options])

  const selectables = options.filter((option) => !selected.includes(option.value))

  return (
    <Command onKeyDown={handleKeyDown} className="overflow-visible bg-transparent">
      <div
        className="group rounded-md border border-input px-3 py-2 text-sm ring-offset-background focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2"
      >
        <div className="flex flex-wrap gap-1">
          {selected.map((tag) => {
            const option = options.find(o => o.value === tag);
            return (
              <Badge key={tag} variant="secondary">
                {option ? option.label : tag}
                <button
                  className="ml-1 rounded-full outline-none ring-offset-background focus:ring-2 focus:ring-ring focus:ring-offset-2"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleUnselect(tag)
                    }
                  }}
                  onMouseDown={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                  }}
                  onClick={() => handleUnselect(tag)}
                  type="button" // Prevent form submission
                >
                  <X className="size-3 text-muted-foreground hover:text-foreground" />
                </button>
              </Badge>
            )
          })}
          {/* Avoid having the "Search" Icon */}
          <CommandPrimitive.Input
            ref={inputRef}
            value={inputValue}
            onValueChange={setInputValue}
            onBlur={() => setOpen(false)}
            onFocus={() => setOpen(true)}
            placeholder={placeholder}
            className="ml-2 flex-1 bg-transparent outline-none placeholder:text-muted-foreground"
          />
        </div>
      </div>
      <div className="relative mt-2">
        {open && selectables.length > 0 ? (
          <div className="absolute top-0 z-10 w-full rounded-md border bg-popover text-popover-foreground shadow-md outline-none animate-in">
            <CommandList>
                <CommandGroup className="h-full max-h-[200px] overflow-auto">
                  {selectables.map((option) => {
                    return (
                      <CommandItem
                        key={option.value}
                        onMouseDown={(e) => {
                          e.preventDefault()
                          e.stopPropagation()
                        }}
                        onSelect={() => {
                          setInputValue("")
                          onChange([...selected, option.value])
                        }}
                        className={"cursor-pointer"}
                      >
                        {option.label}
                      </CommandItem>
                    )
                  })}
                </CommandGroup>
            </CommandList>
          </div>
        ) : null}
      </div>
    </Command>
  )
}
