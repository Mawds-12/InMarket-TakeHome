const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🔍 Checking for dependency version mismatches...');

// Get platform-specific pip path
function getPipPath() {
  const isWindows = process.platform === 'win32';
  return isWindows ? 'Scripts\\pip.exe' : 'bin/pip';
}

// Simple version comparison - returns true if installed < required (outdated)
function isOutdated(installed, required) {
  const parseVersion = (version) => {
    const cleanVersion = version.replace(/[a-zA-Z].*$/, '');
    return cleanVersion.split('.').map(num => parseInt(num, 10) || 0);
  };
  
  const installedParts = parseVersion(installed);
  const requiredParts = parseVersion(required);
  
  const maxLength = Math.max(installedParts.length, requiredParts.length);
  while (installedParts.length < maxLength) installedParts.push(0);
  while (requiredParts.length < maxLength) requiredParts.push(0);
  
  for (let i = 0; i < maxLength; i++) {
    if (installedParts[i] < requiredParts[i]) {
      return true; // outdated
    } else if (installedParts[i] > requiredParts[i]) {
      return false; // newer, not outdated
    }
  }
  return false; // equal, not outdated
}

// Check Python requirements
function checkPythonDeps() {
  const requirementsPath = path.join(__dirname, '../Backend/requirements.txt');
  
  if (!fs.existsSync(requirementsPath)) {
    console.log('❌ Backend requirements.txt not found');
    return false;
  }
  
  if (!checkVenv()) {
    console.log('❌ Python virtual environment not found, will create');
    return false;
  }
  
  try {
    // Get installed packages
    const pipPath = getPipPath();
    const installedPackages = execSync(`${pipPath} list --format=freeze`, { 
      encoding: 'utf8',
      cwd: path.join(__dirname, '../venv')
    });
    
    // Parse requirements.txt
    const requirements = fs.readFileSync(requirementsPath, 'utf8');
    const requiredPackages = {};
    
    requirements.split('\n').forEach(line => {
      const match = line.match(/^([a-zA-Z0-9\-_.]+)[>=<==]+([0-9.]+[^\s]*)/);
      if (match && !line.startsWith('#')) {
        requiredPackages[match[1].toLowerCase()] = match[2];
      }
    });
    
    // Parse installed packages
    const installed = {};
    installedPackages.split('\n').forEach(line => {
      const match = line.match(/^([a-zA-Z0-9\-_.]+)==([0-9.]+[^\s]*)/);
      if (match) {
        installed[match[1].toLowerCase()] = match[2];
      }
    });
    
    // Check for missing or outdated packages
    let needsUpdate = false;
    const packagesToUpdate = [];
    
    Object.keys(requiredPackages).forEach(pkg => {
      const requiredVersion = requiredPackages[pkg];
      const installedVersion = installed[pkg];
      
      if (!installedVersion) {
        console.log(`❌ Missing package: ${pkg}`);
        packagesToUpdate.push(`${pkg}==${requiredVersion}`);
        needsUpdate = true;
      } else if (isOutdated(installedVersion, requiredVersion)) {
        console.log(`⚠️  Outdated package: ${pkg} (installed: ${installedVersion}, required: ${requiredVersion})`);
        packagesToUpdate.push(`${pkg}==${requiredVersion}`);
        needsUpdate = true;
      } else {
        console.log(`✅ Package ${pkg} OK (installed: ${installedVersion})`);
      }
    });
    
    if (needsUpdate) {
      console.log('🔧 Updating Python packages...');
      try {
        const pipPath = getPipPath();
        const installCmd = `${pipPath} install ${packagesToUpdate.join(' ')}`;
        execSync(installCmd, { stdio: 'inherit', cwd: path.join(__dirname, '../venv') });
        console.log('✅ Python packages updated');
      } catch (error) {
        console.log('❌ Failed to update Python packages:', error.message);
        return false;
      }
    } else {
      console.log('✅ All Python packages up to date');
    }
    
    return true;
  } catch (error) {
    console.log('❌ Failed to check Python dependencies:', error.message);
    return false;
  }
}

// Check if venv exists
function checkVenv() {
  const venvPath = path.join(__dirname, '../venv');
  return fs.existsSync(venvPath);
}

// Check if Frontend deps are installed
function checkFrontendDeps() {
  const nodeModulesPath = path.join(__dirname, '../FrontEnd/node_modules');
  return fs.existsSync(nodeModulesPath);
}

// Main check function
function main() {
  let needsPythonSetup = false;
  let needsFrontendSetup = false;
  
  // Check Python environment
  if (!checkVenv()) {
    console.log('❌ Python virtual environment not found');
    needsPythonSetup = true;
  } else if (!checkPythonDeps()) {
    needsPythonSetup = true;
  }
  
  // Check Frontend dependencies
  if (!checkFrontendDeps()) {
    console.log('❌ Frontend dependencies not found');
    needsFrontendSetup = true;
  }
  
  // Setup if needed
  if (needsPythonSetup || needsFrontendSetup) {
    console.log('🔧 Setting up missing dependencies...');
    
    if (needsPythonSetup) {
      try {
        execSync('python -m venv venv && venv\\Scripts\\pip.exe install -r Backend/requirements.txt', { 
          stdio: 'inherit',
          cwd: path.join(__dirname, '..')
        });
        console.log('✅ Python dependencies installed');
      } catch (error) {
        console.log('❌ Failed to install Python dependencies:', error.message);
        process.exit(1);
      }
    }
    
    if (needsFrontendSetup) {
      try {
        execSync('npm install', { 
          stdio: 'inherit',
          cwd: path.join(__dirname, '../FrontEnd')
        });
        console.log('✅ Frontend dependencies installed');
      } catch (error) {
        console.log('❌ Failed to install Frontend dependencies:', error.message);
        process.exit(1);
      }
    }
  } else {
    console.log('✅ All dependencies up to date');
  }
}

main();
