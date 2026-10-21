"use client";

import { useState } from "react";
import { ChatPanel } from "@/components/chat-panel";
import { DocumentsPanel } from "@/components/documents-panel";
import { EchoCard } from "@/components/echo-card";
import { FilesCard } from "@/components/files-card";
import { GreetCard } from "@/components/greet-card";
import { SettingsPanel } from "@/components/settings-panel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Settings } from "@/lib/api";

export default function Home() {
  const [settings, setSettings] = useState<Settings>({
    model: "gpt-4o-mini",
    k: 4,
    style: "concise",
    showSources: true,
  });

  return (
    <main className="mx-auto w-full max-w-5xl space-y-6 p-6">
      <h1 className="text-2xl font-semibold">RAG Notes Bot</h1>
      <Tabs defaultValue="bot">
        <TabsList>
          <TabsTrigger value="bot">Notes bot</TabsTrigger>
          <TabsTrigger value="basics">Basics</TabsTrigger>
        </TabsList>

        <TabsContent value="bot" className="grid gap-6 pt-4 md:grid-cols-[1fr_18rem]">
          <ChatPanel settings={settings} />
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Settings</CardTitle>
              </CardHeader>
              <CardContent>
                <SettingsPanel value={settings} onChange={setSettings} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Knowledge base</CardTitle>
              </CardHeader>
              <CardContent>
                <DocumentsPanel />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="basics" className="grid gap-6 pt-4 md:grid-cols-3">
          <EchoCard />
          <GreetCard />
          <FilesCard />
        </TabsContent>
      </Tabs>
    </main>
  );
}
