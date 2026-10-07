// Draft cheap, finish sharp: four 1K drafts on Nano Banana 2 Lite ($0.01 each), then the chosen
// draft goes to Nano Banana Pro as a reference for a 4K final ($0.03). Total: $0.07.
import { NanoBanana, price, save } from "../nanobanana.mjs";

const client = new NanoBanana();
const idea = "A hand-drawn travel poster of Lisbon trams climbing a hill, warm evening palette, title text 'LISBOA'";

const drafts = await client.generate(idea, { model: "nano-banana-2-lite", aspectRatio: "3:4", n: 4 });
const draftPaths = await save(drafts, "lisbon-draft");
console.log("drafts:", draftPaths.join(", "));

const pick = process.argv[2] ?? draftPaths[0]; // pass the path of the draft you like
const [final] = await client.edit(
  "Redraw this poster as a finished print: same layout and palette, crisp lettering, fine paper texture",
  [pick],
  { model: "nano-banana-pro", aspectRatio: "3:4", resolution: "4k" },
);
console.log("final:", (await save([final], "lisbon-final"))[0]);

const total = price("nano-banana-2-lite", "1k", drafts.length) + price("nano-banana-pro", "4k", 1);
console.log(`spent about $${total.toFixed(2)}`);
