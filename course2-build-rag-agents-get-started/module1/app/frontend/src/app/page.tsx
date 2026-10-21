"use client";

import { AskPanel } from "@/components/ask-panel";
import { ChunksPanel } from "@/components/chunks-panel";
import { SearchPanel } from "@/components/search-panel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">RAG Lab: Innovatech Policies</h1>
        <p className="text-sm text-muted-foreground">
          Split, search and ask. Change one thing at a time and watch what happens.
        </p>
      </div>
      <Tabs defaultValue="chunks">
        <TabsList>
          <TabsTrigger value="chunks">1. Chunks</TabsTrigger>
          <TabsTrigger value="search">2. Search</TabsTrigger>
          <TabsTrigger value="ask">3. Ask</TabsTrigger>
        </TabsList>
        <TabsContent value="chunks" className="pt-4">
          <ChunksPanel />
        </TabsContent>
        <TabsContent value="search" className="pt-4">
          <SearchPanel />
        </TabsContent>
        <TabsContent value="ask" className="pt-4">
          <AskPanel />
        </TabsContent>
      </Tabs>
    </main>
  );
}
