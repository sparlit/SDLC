const content = "```json\n{\"nodes\": [], \"connections\": {}}\n```";
const match = content.match(/```json\n([\s\S]*?)\n```/);
const jsonStr = match ? match[1] : content;
console.log('JSON STR:', jsonStr);
console.log('PARSED:', JSON.parse(jsonStr.trim()));
