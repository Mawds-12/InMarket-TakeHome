#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Environment file mappings
const envMappings = [
  {
    example: path.join(__dirname, '..', 'MCP', '.env.example'),
    target: path.join(__dirname, '..', 'MCP', '.env'),
    name: 'MCP/.env',
    description: 'MCP Service - External APIs and configuration'
  },
  {
    example: path.join(__dirname, '..', 'Backend', '.env.example'),
    target: path.join(__dirname, '..', 'Backend', '.env'),
    name: 'Backend/.env',
    description: 'Backend - LLM keys and internal services'
  },
  {
    example: path.join(__dirname, '..', 'FrontEnd', '.env.example'),
    target: path.join(__dirname, '..', 'FrontEnd', '.env.local'),
    name: 'FrontEnd/.env.local',
    description: 'Frontend - Backend connection and feature flags'
  }
];

// Variable descriptions from ENV_REFERENCE.md
const variableDescriptions = {
  // MCP variables
  'COURTLISTENER_API_KEY': 'CourtListener API key (get at https://www.courtlistener.com/help/api/)',
  'OPEN_STATES_API_KEY': 'Open States API v3 key (get at https://openstates.org/accounts/register/)',
  'IPINFO_TOKEN': 'IPinfo access token (get at https://ipinfo.io/signup/)',
  'MCP_PORT': 'Port the MCP service listens on (default: 8001)',
  'MCP_CASE_RESULT_LIMIT': 'Maximum raw case results to return (default: 10)',
  'MCP_DOC_TEXT_CHAR_LIMIT': 'Maximum characters from document text (default: 6000)',
  
  // Backend variables
  'ANTHROPIC_API_KEY': 'Anthropic API key (get at https://console.anthropic.com/)',
  'ANTHROPIC_MODEL': 'Claude model to use (recommended: claude-sonnet-4-20250514)',
  'MCP_BASE_URL': 'Base URL of MCP service (default: http://localhost:8001)',
  'BACKEND_PORT': 'Backend port (default: 8000)',
  
  // Frontend variables
  'BACKEND_URL': 'Backend service URL (default: http://localhost:8000)',
  'NEXT_PUBLIC_SHOW_DEBUG_TOGGLE': 'Show debug toggle in UI (true/false, default: false)'
};

// Setup readline interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Helper function to ask questions
function askQuestion(prompt) {
  return new Promise((resolve) => {
    rl.question(prompt, (answer) => {
      resolve(answer.trim());
    });
  });
}

// Parse .env file into key-value pairs
function parseEnvFile(content) {
  const lines = content.split('\n');
  const variables = {};
  
  lines.forEach(line => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const equalIndex = trimmed.indexOf('=');
      if (equalIndex > 0) {
        const key = trimmed.substring(0, equalIndex).trim();
        const value = trimmed.substring(equalIndex + 1).trim();
        variables[key] = value;
      }
    }
  });
  
  return variables;
}

// Update .env file with new values
function updateEnvFile(filePath, variables) {
  let content = fs.readFileSync(filePath, 'utf8');
  
  Object.entries(variables).forEach(([key, value]) => {
    const regex = new RegExp(`^${key}=.*$`, 'm');
    if (regex.test(content)) {
      content = content.replace(regex, `${key}=${value}`);
    } else {
      content += `\n${key}=${value}`;
    }
  });
  
  fs.writeFileSync(filePath, content);
}

// Check if a value is a placeholder
function isPlaceholder(value) {
  return value === '' || 
         value === '""' || 
         value === "''" || 
         value.includes('your_') || 
         value.includes('YOUR_') ||
         value === 'YOUR_API_KEY_HERE' ||
         value === 'your_api_key_here';
}

// Main setup function
async function setupEnvironment() {
  console.log('🔍 Checking environment files...\n');
  
  const filesToPopulate = [];
  
  // Step 1: Ensure all .env files exist and check for placeholders
  for (const { example, target, name, description } of envMappings) {
    console.log(`\n--- ${description} ---`);
    
    // Create file if it doesn't exist
    if (!fs.existsSync(target)) {
      if (!fs.existsSync(example)) {
        console.log(`❌ Missing both ${name} and ${path.basename(example)}`);
        continue;
      }
      fs.copyFileSync(example, target);
      console.log(`✅ Created ${name} from example`);
    } else {
      console.log(`✓ ${name} exists`);
    }
    
    // Check for placeholder values
    const content = fs.readFileSync(target, 'utf8');
    const variables = parseEnvFile(content);
    const placeholders = Object.entries(variables)
      .filter(([key, value]) => isPlaceholder(value))
      .map(([key]) => key);
    
    if (placeholders.length > 0) {
      filesToPopulate.push({ target, name, description, variables, placeholders });
      console.log(`⚠️  Found ${placeholders.length} variables to configure`);
    } else {
      console.log(`✅ All variables configured`);
    }
  }
  
  // Step 2: Interactive population
  if (filesToPopulate.length === 0) {
    console.log('\n🎉 All environment files are ready!\n');
    rl.close();
    return;
  }
  
  console.log('\n📝 Let\'s configure your environment variables:');
  console.log('   (Press Enter to skip, Ctrl+C to exit)\n');
  
  for (const { target, name, description, variables, placeholders } of filesToPopulate) {
    console.log(`\n=== ${description} ===`);
    const updates = {};
    
    for (const key of placeholders) {
      const description = variableDescriptions[key] || 'No description available';
      console.log(`\n📋 ${key}`);
      console.log(`   ${description}`);
      
      const response = await askQuestion(`${key}: `);
      
      if (response) {
        updates[key] = response;
        console.log(`✓ Set ${key}`);
      } else {
        console.log(`- Skipped ${key}`);
      }
    }
    
    if (Object.keys(updates).length > 0) {
      updateEnvFile(target, updates);
      console.log(`\n✅ Updated ${name}`);
    } else {
      console.log(`\n- No changes to ${name}`);
    }
  }
  
  console.log('\n🎉 Environment setup complete!');
  console.log('   You can now run: npm run dev\n');
  rl.close();
}

// Handle Ctrl+C gracefully
rl.on('SIGINT', () => {
  console.log('\n\n❌ Setup cancelled by user');
  rl.close();
  process.exit(0);
});

// Run the setup
setupEnvironment().catch(error => {
  console.error('❌ Setup failed:', error.message);
  rl.close();
  process.exit(1);
});
