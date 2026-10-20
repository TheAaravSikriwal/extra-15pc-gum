// The Extra 15pc Gum drag plugin for Gazebo Harmonic. GPL-3.0.
//
// Body drag: F = -1/2 rho |v| v, where v is the link's velocity less the wind's and the area
// is the drag area (drag coefficient times frontal area) the sizing model uses for this module
// combination. The parachute: once fired, it waits out its ejection delay, then its canopy's
// drag area grows in a straight line to full over its opening time, adding to the body's.
//
// This is exactly src/pcs14/flight/drag.py, whose tests are the plugin's specification.
//
// SDF, inside the model:
//   <plugin filename="pcs14-drag" name="pcs14::systems::Drag">
//     <link_name>base_link</link_name>
//     <drag_area>0.0202</drag_area>          m^2
//     <wind_topic>/pcs14/wind</wind_topic>   gz.msgs.Vector3d, m/s in the world frame
//     <chute>                                optional
//       <canopy_area>1.89</canopy_area>      m^2
//       <ejection_s>0.2</ejection_s>
//       <opening_s>1.0</opening_s>
//       <fire_topic>/pcs14/chute/fire</fire_topic>   gz.msgs.Empty
//     </chute>
//   </plugin>
// The wind starts from the world's <wind><linear_velocity>.

#include <algorithm>
#include <chrono>
#include <cmath>
#include <mutex>
#include <optional>
#include <string>

#include <gz/math/Vector3.hh>
#include <gz/msgs/empty.pb.h>
#include <gz/msgs/vector3d.pb.h>
#include <gz/plugin/Register.hh>
#include <gz/sim/Link.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/System.hh>
#include <gz/sim/components/LinearVelocity.hh>
#include <gz/sim/components/Wind.hh>
#include <gz/transport/Node.hh>

namespace pcs14::systems
{
constexpr double kAirDensity = 1.225;  // kg/m^3, the sizing model's standard sea-level air

class Drag : public gz::sim::System,
             public gz::sim::ISystemConfigure,
             public gz::sim::ISystemPreUpdate
{
public:
  void Configure(const gz::sim::Entity &entity,
                 const std::shared_ptr<const sdf::Element> &sdf,
                 gz::sim::EntityComponentManager &ecm,
                 gz::sim::EventManager &) override
  {
    gz::sim::Model model(entity);
    const auto linkName = sdf->Get<std::string>("link_name", "base_link").first;
    this->link = gz::sim::Link(model.LinkByName(ecm, linkName));
    this->link.EnableVelocityChecks(ecm, true);
    this->dragArea = sdf->Get<double>("drag_area", 0.0).first;

    // the world's starting wind
    const auto windEntity = ecm.EntityByComponents(gz::sim::components::Wind());
    if (windEntity != gz::sim::kNullEntity)
    {
      if (const auto *v = ecm.Component<gz::sim::components::WorldLinearVelocity>(windEntity))
        this->wind = v->Data();
    }
    const auto windTopic = sdf->Get<std::string>("wind_topic", "/pcs14/wind").first;
    this->node.Subscribe(windTopic, &Drag::OnWind, this);

    if (sdf->HasElement("chute"))
    {
      auto chute = sdf->FindElement("chute");
      this->canopyArea = chute->Get<double>("canopy_area", 0.0).first;
      this->ejectionS = chute->Get<double>("ejection_s", 0.0).first;
      this->openingS = std::max(chute->Get<double>("opening_s", 1.0).first, 1e-3);
      const auto fireTopic = chute->Get<std::string>("fire_topic", "/pcs14/chute/fire").first;
      this->node.Subscribe(fireTopic, &Drag::OnFire, this);
    }
  }

  void PreUpdate(const gz::sim::UpdateInfo &info, gz::sim::EntityComponentManager &ecm) override
  {
    if (info.paused || !this->link.Valid(ecm))
      return;
    const double now = std::chrono::duration<double>(info.simTime).count();
    gz::math::Vector3d wind;
    {
      std::lock_guard<std::mutex> lock(this->mutex);
      wind = this->wind;
      if (this->fireRequested && !this->firedAt)
        this->firedAt = now;
    }
    double area = this->dragArea;
    if (this->firedAt)
    {
      const double since = now - *this->firedAt;
      if (since >= this->ejectionS)
        area += this->canopyArea * std::min((since - this->ejectionS) / this->openingS, 1.0);
    }
    const auto velocity = this->link.WorldLinearVelocity(ecm);
    if (!velocity || area <= 0.0)
      return;
    const gz::math::Vector3d rel = *velocity - wind;
    const gz::math::Vector3d force = -0.5 * kAirDensity * area * rel.Length() * rel;
    this->link.AddWorldForce(ecm, force);
  }

private:
  void OnWind(const gz::msgs::Vector3d &msg)
  {
    std::lock_guard<std::mutex> lock(this->mutex);
    this->wind.Set(msg.x(), msg.y(), msg.z());
  }

  void OnFire(const gz::msgs::Empty &)
  {
    std::lock_guard<std::mutex> lock(this->mutex);
    this->fireRequested = true;
  }

  gz::sim::Link link{gz::sim::kNullEntity};
  double dragArea{0.0};
  double canopyArea{0.0};
  double ejectionS{0.0};
  double openingS{1.0};
  std::optional<double> firedAt;
  bool fireRequested{false};
  gz::math::Vector3d wind{0, 0, 0};
  std::mutex mutex;
  gz::transport::Node node;
};
}  // namespace pcs14::systems

GZ_ADD_PLUGIN(pcs14::systems::Drag,
              gz::sim::System,
              gz::sim::ISystemConfigure,
              gz::sim::ISystemPreUpdate)
GZ_ADD_PLUGIN_ALIAS(pcs14::systems::Drag, "pcs14::systems::Drag")
