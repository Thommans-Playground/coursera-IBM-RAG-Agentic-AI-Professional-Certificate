"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import type { Settings } from "@/lib/api";

type Props = { value: Settings; onChange: (next: Settings) => void };

export function SettingsPanel({ value, onChange }: Props) {
  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <Label>Model (dropdown)</Label>
        <Select value={value.model} onValueChange={(m) => m && onChange({ ...value, model: m })}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="gpt-4o-mini">gpt-4o-mini</SelectItem>
            <SelectItem value="gpt-4o">gpt-4o</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Chunks to retrieve, k = {value.k} (slider)</Label>
        {/* Whole-number min, max and step keep the value an integer. */}
        <Slider
          min={1}
          max={10}
          step={1}
          value={[value.k]}
          onValueChange={(v) => onChange({ ...value, k: Array.isArray(v) ? v[0] : v })}
        />
      </div>

      <div className="space-y-2">
        <Label>Answer style (radio: pick exactly one)</Label>
        <RadioGroup value={value.style} onValueChange={(s) => onChange({ ...value, style: s as Settings["style"] })}>
          <div className="flex items-center gap-2">
            <RadioGroupItem value="concise" id="concise" />
            <Label htmlFor="concise">Concise</Label>
          </div>
          <div className="flex items-center gap-2">
            <RadioGroupItem value="detailed" id="detailed" />
            <Label htmlFor="detailed">Detailed</Label>
          </div>
        </RadioGroup>
      </div>

      <div className="flex items-center gap-2">
        <Checkbox
          id="sources"
          checked={value.showSources}
          onCheckedChange={(c) => onChange({ ...value, showSources: c === true })}
        />
        <Label htmlFor="sources">Show sources (checkbox)</Label>
      </div>
    </div>
  );
}
