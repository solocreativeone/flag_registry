const hre = require("hardhat");

async function main() {
  console.log(`Deploying FlagRegistry to network: ${hre.network.name}...`);

  const FlagRegistry = await hre.ethers.getContractFactory("FlagRegistry");
  const registry = await FlagRegistry.deploy();
  await registry.waitForDeployment();

  const address = await registry.getAddress();
  console.log(`FlagRegistry deployed to: ${address}`);
  console.log(`\nNext step - verify on Arbiscan:`);
  console.log(`npx hardhat verify --network arbitrumSepolia ${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
