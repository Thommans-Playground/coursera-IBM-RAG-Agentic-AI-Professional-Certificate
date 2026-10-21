"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { postJson } from "@/lib/api";

export function GreetCard() {
  const [name, setName] = useState("");
  const [times, setTimes] = useState(1);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function run() {
    setError("");
    try {
      const data = await postJson<{ message: string }>("/api/greet", { name, times });
      setMessage(data.message);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Greet (a text input and a number input)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Label htmlFor="name">Name</Label>
        <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
        <Label htmlFor="times">Times (1 to 10)</Label>
        <Input id="times" type="number" value={times} onChange={(e) => setTimes(Number(e.target.value))} />
        <Button onClick={run}>Greet</Button>
        {error && <p className="text-sm text-destructive">{error}</p>}
        {message && <p className="text-sm">{message}</p>}
      </CardContent>
    </Card>
  );
}
