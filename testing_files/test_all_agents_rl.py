#!/usr/bin/env python3
"""
Comprehensive Test Script for All RL-Enhanced Agents
Tests all 7 agents with RL learning capabilities
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, List


class RLAgentTester:
    """Comprehensive tester for all RL-enhanced agents"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {}
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_agent_endpoint(self, agent_name: str, endpoint: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test an individual agent endpoint"""
        print(f"🧪 Testing {agent_name}...")
        
        start_time = time.time()
        
        try:
            async with self.session.post(
                f"{self.base_url}{endpoint}",
                json=test_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                response_data = await response.json()
                end_time = time.time()
                
                # Check for RL learning data
                has_rl_data = 'rl_learning' in response_data and response_data['rl_learning'] is not None
                
                result = {
                    'agent': agent_name,
                    'endpoint': endpoint,
                    'status_code': response.status,
                    'success': response_data.get('success', False),
                    'response_time': end_time - start_time,
                    'has_rl_learning': has_rl_data,
                    'rl_data': response_data.get('rl_learning', {}),
                    'response_length': len(response_data.get('result', '')),
                    'timestamp': datetime.now().isoformat()
                }
                
                if has_rl_data:
                    rl_data = response_data['rl_learning']
                    result['learning_summary'] = {
                        'session_id': rl_data.get('learning_summary', {}).get('session_id', ''),
                        'reward': rl_data.get('learning_summary', {}).get('reward', 0),
                        'q_value': rl_data.get('learning_summary', {}).get('q_value', 0)
                    }
                
                print(f"✅ {agent_name}: {'SUCCESS' if result['success'] else 'FAILED'} "
                      f"({result['response_time']:.2f}s) "
                      f"{'[RL: ✅]' if has_rl_data else '[RL: ❌]'}")
                
                return result
                
        except Exception as e:
            print(f"❌ {agent_name}: ERROR - {str(e)}")
            return {
                'agent': agent_name,
                'endpoint': endpoint,
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
    
    async def test_rl_system_endpoints(self) -> Dict[str, Any]:
        """Test RL system monitoring endpoints"""
        print(f"\n🔬 Testing RL System Endpoints...")
        
        rl_tests = {}
        
        # Test RL status endpoint
        try:
            async with self.session.get(f"{self.base_url}/api/rl/status") as response:
                rl_tests['status'] = {
                    'success': response.status == 200,
                    'data': await response.json() if response.status == 200 else None
                }
                print(f"✅ RL Status: {'SUCCESS' if rl_tests['status']['success'] else 'FAILED'}")
        except Exception as e:
            rl_tests['status'] = {'success': False, 'error': str(e)}
            print(f"❌ RL Status: ERROR - {str(e)}")
        
        # Test RL global insights
        try:
            async with self.session.get(f"{self.base_url}/api/rl/global-insights") as response:
                rl_tests['global_insights'] = {
                    'success': response.status == 200,
                    'data': await response.json() if response.status == 200 else None
                }
                print(f"✅ Global Insights: {'SUCCESS' if rl_tests['global_insights']['success'] else 'FAILED'}")
        except Exception as e:
            rl_tests['global_insights'] = {'success': False, 'error': str(e)}
            print(f"❌ Global Insights: ERROR - {str(e)}")
        
        # Test RL sync
        try:
            async with self.session.post(f"{self.base_url}/api/rl/sync") as response:
                rl_tests['sync'] = {
                    'success': response.status == 200,
                    'data': await response.json() if response.status == 200 else None
                }
                print(f"✅ RL Sync: {'SUCCESS' if rl_tests['sync']['success'] else 'FAILED'}")
        except Exception as e:
            rl_tests['sync'] = {'success': False, 'error': str(e)}
            print(f"❌ RL Sync: ERROR - {str(e)}")
        
        return rl_tests
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test of all RL-enhanced agents"""
        
        print("🚀 Starting Comprehensive RL Agent Test")
        print("=" * 60)
        
        # Test data for each agent
        test_configurations = {
            'Agent 1 - Channel Auditor': {
                'endpoint': '/api/agent1/audit-channel',
                'data': {
                    'channel_urls': ['https://youtube.com/@MrBeast'],
                    'user_query': 'Perform a quick audit on this channel for RL testing'
                }
            },
            'Agent 2 - Title Auditor': {
                'endpoint': '/api/agent2/audit-titles', 
                'data': {
                    'video_urls': ['https://www.youtube.com/watch?v=dQw4w9WgXcQ'],
                    'user_query': 'Analyze this video for RL testing'
                }
            },
            'Agent 3 - Script Generator': {
                'endpoint': '/api/agent3/generate-script',
                'data': {
                    'topic': 'RL Testing for YouTube Agents',
                    'total_words': 500,
                    'tone': 'conversational'
                }
            },
            'Agent 4 - Script to Scene': {
                'endpoint': '/api/agent4/script-to-prompts',
                'data': {
                    'script': 'Hello everyone, welcome to my channel. Today we are testing RL learning.',
                    'user_query': 'Convert this simple script to scene prompts for RL testing'
                }
            },
            'Agent 5 - Ideas Generator': {
                'endpoint': '/api/agent5/generate-ideas',
                'data': {
                    'winning_videos_data': 'Sample winning video data for testing',
                    'user_query': 'Generate 3 title-thumbnail ideas for RL testing'
                }
            },
            'Agent 6 - Roadmap Generator': {
                'endpoint': '/api/agent6/generate-roadmap',
                'data': {
                    'niche': 'AI & Technology',
                    'user_query': 'Create a simple 5-video roadmap for RL testing'
                }
            },
            'Agent 7 - Videos Fetcher': {
                'endpoint': '/api/fifty-videos/fetch-links',
                'data': {
                    'input': 'UC-lHJZR3Gqxm24_Vd_AJ5Yw',
                    'user_query': 'Fetch some video links for RL testing'
                }
            }
        }
        
        # Test each agent
        agent_results = {}
        for agent_name, config in test_configurations.items():
            agent_results[agent_name] = await self.test_agent_endpoint(
                agent_name, 
                config['endpoint'], 
                config['data']
            )
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        # Test RL system endpoints
        rl_results = await self.test_rl_system_endpoints()
        
        # Compile comprehensive results
        comprehensive_results = {
            'test_summary': {
                'total_agents_tested': len(agent_results),
                'successful_agents': len([r for r in agent_results.values() if r.get('success', False)]),
                'agents_with_rl': len([r for r in agent_results.values() if r.get('has_rl_learning', False)]),
                'rl_system_tests': len([r for r in rl_results.values() if r.get('success', False)]),
                'test_timestamp': datetime.now().isoformat()
            },
            'agent_results': agent_results,
            'rl_system_results': rl_results,
            'overall_success': all(r.get('success', False) for r in agent_results.values())
        }
        
        return comprehensive_results
    
    def print_final_report(self, results: Dict[str, Any]) -> None:
        """Print comprehensive test report"""
        
        print("\n" + "=" * 60)
        print("🎯 COMPREHENSIVE RL INTEGRATION TEST REPORT")
        print("=" * 60)
        
        summary = results['test_summary']
        
        print(f"\n📊 **Test Summary:**")
        print(f"   Total Agents Tested: {summary['total_agents_tested']}/7")
        print(f"   Successful Responses: {summary['successful_agents']}/7")
        print(f"   Agents with RL Learning: {summary['agents_with_rl']}/7") 
        print(f"   RL System Tests Passed: {summary['rl_system_tests']}/3")
        
        print(f"\n🤖 **Individual Agent Results:**")
        for agent_name, result in results['agent_results'].items():
            status = "✅ SUCCESS" if result.get('success', False) else "❌ FAILED"
            rl_status = "🧠 RL: ✅" if result.get('has_rl_learning', False) else "🧠 RL: ❌"
            response_time = f"{result.get('response_time', 0):.2f}s"
            
            print(f"   {agent_name}: {status} ({response_time}) {rl_status}")
            
            if result.get('has_rl_learning', False) and 'learning_summary' in result:
                ls = result['learning_summary']
                print(f"     └─ Session: {ls.get('session_id', 'N/A')}")
                print(f"     └─ Reward: {ls.get('reward', 0):.3f}")
                print(f"     └─ Q-Value: {ls.get('q_value', 0):.3f}")
        
        print(f"\n🔬 **RL System Tests:**")
        for test_name, result in results['rl_system_results'].items():
            status = "✅ SUCCESS" if result.get('success', False) else "❌ FAILED"
            print(f"   {test_name.title()}: {status}")
        
        # Overall assessment
        overall_success = results['overall_success']
        agents_with_rl = summary['agents_with_rl']
        
        print(f"\n🎉 **INTEGRATION STATUS:**")
        if overall_success and agents_with_rl >= 6:
            print("   🏆 EXCELLENT: RL system fully integrated and working!")
        elif agents_with_rl >= 4:
            print("   ⚠️  GOOD: Most agents have RL, some issues to resolve")
        else:
            print("   ❌ NEEDS WORK: RL integration incomplete")
        
        print(f"\n💡 **Next Steps:**")
        if overall_success and agents_with_rl >= 6:
            print("   • System ready for production use")
            print("   • Monitor learning progress over time")  
            print("   • Collect user feedback for faster learning")
        else:
            print("   • Fix failing agents and RL integration issues")
            print("   • Ensure all agents have @rl_enhanced decorator")
            print("   • Check database connections and RL system setup")


async def main():
    """Main test execution"""
    
    print("🧠 RL-Enhanced YouTube Agents - Comprehensive Test")
    print("🔗 Testing all 7 agents with reinforcement learning capabilities")
    print()
    
    async with RLAgentTester() as tester:
        try:
            results = await tester.run_comprehensive_test()
            
            # Save results to file
            with open('rl_test_results.json', 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Print final report
            tester.print_final_report(results)
            
            print(f"\n💾 Detailed results saved to: rl_test_results.json")
            
        except KeyboardInterrupt:
            print("\n⚠️ Test interrupted by user")
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")


if __name__ == "__main__":
    # Run the comprehensive test
    asyncio.run(main())
