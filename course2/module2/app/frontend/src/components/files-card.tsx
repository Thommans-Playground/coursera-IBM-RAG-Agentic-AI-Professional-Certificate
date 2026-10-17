"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { postFiles } from "@/lib/api";

export function FilesCard() {
  const [result, setResult] = useState<{ count: number; names: string[] } | null>(null);

  async function onPick(files: FileList | null) {
    if (!files || files.length === 0) return;
    setResult(await postFiles("/api/count-files", files));
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Count files (file upload)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Label htmlFor="files">Choose one or more files</Label>
        <Input id="files" type="file" multiple onChange={(e) => onPick(e.target.files)} />
        {result && (
          <p className="text-sm">
            {result.count} file(s): {result.names.join(", ")}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
