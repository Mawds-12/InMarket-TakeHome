#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const envMappings = [
  {
    example: path.join(__dirname, '..', 'MCP', '.env.example'),
    target: path.join(__dirname, '..', 'MCP', '.env'),
    name: 'MCP/.env'
  },
  {
    example: path.join(__dirname, '..', 'Backend', '.env.example'),
    target: path.join(__dirname, '..', 'Backend', '.env'),
    name: 'Backend/.env'
  },
  {
    example: path.join(__dirname, '..', 'FrontEnd', '.env.example'),
    target: path.join(__dirname, '..', 'FrontEnd', '.env.local'),
    name: 'FrontEnd/.env.local'
  }
];

let copied = false;

console.log('🔍 Checking environment files...\n');

envMappings.forEach(({ example, target, name }) => {
  if (!fs.existsSync(target)) {
    try {
      fs.copyFileSync(example, target);
      console.log(`✅ Created ${name} from .env.example`);
      copied = true;
    } catch (error) {
      console.error(`❌ Failed to copy ${name}: ${error.message}`);
      process.exit(1);
    }
  } else {
    console.log(`✓ ${name} already exists`);
  }
});

if (copied) {
  console.log('\n⚠️  Please fill in your API keys in the newly created .env files before running the services.');
  console.log('   See Documentation/ENV_REFERENCE.md for details on which keys are needed.\n');
} else {
  console.log('\n✓ All environment files are ready.\n');
}
