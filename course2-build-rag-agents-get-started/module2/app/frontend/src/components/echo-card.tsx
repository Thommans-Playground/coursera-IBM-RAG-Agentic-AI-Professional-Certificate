"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { postJson } from "@/lib/api";

export function EchoCard() {
  const [text, setText] = useState("");
  const [result, setResult] = useState("");

  async function run() {
    const data = await postJson<{ text: string }>("/api/echo", { text });
    setResult(data.text);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Echo (one text in, one text out)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Label htmlFor="echo-in">Input</Label>
        <Input id="echo-in" value={text} onChange={(e) => setText(e.target.value)} />
        <Button onClick={run}>Submit</Button>
        <Label htmlFor="echo-out">Output</Label>
        <Input id="echo-out" value={result} readOnly />
      </CardContent>
    </Card>
  );
}
